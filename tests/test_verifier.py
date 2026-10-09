"""Offline regressions for data boundaries, coverage and failure isolation."""

import asyncio
import copy
import json
import unittest

from hw2 import (CVClaims, CVVerifier, ClaimCheck, Comparison, JobClaim,
                 EducationClaim, claim_ledger, decode_tool_result,
                 guarded_checks, grounded_seniority, identity_rank, score_cvs)


def fixture():
    claims = CVClaims(name="Example Candidate", city="Test City", country="Test Country",
                      industry="Technology", skills=["Python"],
                      jobs=[JobClaim(company="Example Systems", title="Senior Engineer",
                                     start_year=2020, is_current=True,
                                     quote="Senior Engineer, Example Systems 2020-Present")],
                      education=[EducationClaim(school="Example University", degree="BSc",
                                                field="Computer Science", graduation_year=2019,
                                                quote="BSc Example University 2019")])
    profile = {"id": 42, "name": "Example Candidate", "city": "Test City",
               "country": "Test Country", "industry": "Technology",
               "experience": [{"company": "Example Systems", "title": "Engineer",
                               "seniority": "senior", "start_year": 2020,
                               "end_year": None, "is_current": True}],
               "education": [{"school": "Example University", "degree": "BSc",
                              "field": "Computer Science", "end_year": 2019}],
               "skills": [{"name": "Python"}]}
    paths = {"name": "name", "city": "city", "skills.0": "skills.0.name"}
    for row in claim_ledger(claims):
        key = row["key"]
        if key.startswith("jobs."):
            paths[key] = key.replace("jobs.", "experience.")
        if key.startswith("education."):
            paths[key] = key.replace("graduation_year", "end_year")
    comparison = Comparison(checks=[ClaimCheck(key=r["key"], verdict="match",
                                              evidence_path=paths[r["key"]], reason="Matches")
                                    for r in claim_ledger(claims)],
                            job_indices=[0], education_indices=[0])
    return claims, profile, comparison


class EvidenceTests(unittest.TestCase):
    def test_mcp_content_and_fastmcp_wrapper(self):
        expected = [{"id": 42}]
        content = [{"type": "text", "text": json.dumps({"result": expected})}]
        self.assertEqual(decode_tool_result(content), expected)
        self.assertEqual(decode_tool_result({"structuredContent": {"result": expected}}), expected)
        self.assertEqual(decode_tool_result([]), [])
        with self.assertRaises(RuntimeError):
            decode_tool_result({"error": "unknown id"})

    def test_one_year_discrepancy_overrides_positive_model_checks(self):
        claims, profile, comparison = fixture()
        claims.jobs[0].start_year = 2021
        checks = {c["key"]: c for c in guarded_checks(claims, profile, comparison)}
        self.assertEqual(checks["jobs.0.start_year"]["verdict"], "mismatch")

    def test_upgraded_degree_overrides_positive_model_checks(self):
        claims, profile, comparison = fixture()
        claims.education[0].degree = "Master of Science"
        checks = {c["key"]: c for c in guarded_checks(claims, profile, comparison)}
        self.assertEqual(checks["education.0.degree"]["verdict"], "mismatch")
        claims.education[0].degree = "MSc in Computer Science"
        checks = {c["key"]: c for c in guarded_checks(claims, profile, comparison)}
        self.assertEqual(checks["education.0.degree"]["verdict"], "mismatch")

    def test_role_nouns_are_not_seniority_claims(self):
        claims, _, _ = fixture()
        claims.jobs[0].title = "Manager"
        claims.jobs[0].quote = "Manager, Example Systems 2020-Present"
        claims.jobs[0].seniority = "Manager"
        self.assertIsNone(grounded_seniority(claims).jobs[0].seniority)
        claims.jobs[0].seniority = "senior"  # Hallucinated level absent from quote.
        self.assertIsNone(grounded_seniority(claims).jobs[0].seniority)

    def test_allowed_title_seniority_and_skill_subset(self):
        claims, profile, comparison = fixture()
        profile["skills"].append({"name": "Docker"})
        self.assertTrue(all(c["verdict"] == "match"
                            for c in guarded_checks(claims, profile, comparison)))
        profile["experience"][0]["seniority"] = "mid"
        checks = {c["key"]: c for c in guarded_checks(claims, profile, comparison)}
        self.assertEqual(checks["jobs.0.title"]["verdict"], "mismatch")

    def test_known_equivalence_overrides_model_false_alarm(self):
        claims, profile, comparison = fixture()
        claims.skills = ["Microsoft PowerPoint"]
        profile["skills"] = [{"name": "PowerPoint"}]
        for check in comparison.checks:
            if check.key in {"jobs.0.title", "skills.0"}:
                check.verdict = "mismatch"
        checks = {c["key"]: c for c in guarded_checks(claims, profile, comparison)}
        self.assertEqual(checks["jobs.0.title"]["verdict"], "match")
        self.assertEqual(checks["skills.0"]["verdict"], "match")

    def test_missing_or_duplicate_field_cannot_be_accepted(self):
        claims, profile, comparison = fixture()
        comparison.checks.pop()
        with self.assertRaises(ValueError):
            guarded_checks(claims, profile, comparison)
        claims, profile, comparison = fixture()
        comparison.checks.append(comparison.checks[0])
        with self.assertRaises(ValueError):
            guarded_checks(claims, profile, comparison)

    def test_namesake_does_not_win_on_name_and_city_alone(self):
        claims, genuine, _ = fixture()
        wrong = copy.deepcopy(genuine)
        wrong["experience"][0]["company"] = "Unrelated Company"
        wrong["education"][0]["school"] = "Unrelated University"
        genuine["city"] = "Different City"
        self.assertGreater(identity_rank(claims, genuine)[0], identity_rank(claims, wrong)[0])


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_error_isolation_and_three_cv_limit(self):
        class Agent:
            active = 0
            maximum = 0

            async def ainvoke(self, text):
                self.active += 1
                self.maximum = max(self.maximum, self.active)
                try:
                    await asyncio.sleep(0.01)
                    if text == "fail":
                        raise ConnectionError("simulated provider outage")
                    return {"score": float("nan") if text == "nan" else 0.95}
                finally:
                    self.active -= 1

        agent = Agent()
        inputs = {f"document-{i}.pdf": "ok" for i in range(8)}
        inputs.update({"failed.pdf": "fail", "invalid.pdf": "nan"})
        scores = await score_cvs(agent, inputs)
        self.assertEqual(set(scores), set(inputs))
        self.assertEqual(scores["failed.pdf"], 0.35)
        self.assertEqual(scores["invalid.pdf"], 0.35)
        self.assertEqual(scores["document-0.pdf"], 0.95)
        self.assertLessEqual(agent.maximum, 3)

    async def test_wrong_city_search_broadens(self):
        claims, genuine, _ = fixture()
        genuine["city"] = "Real City"
        queries = []
        verifier = object.__new__(CVVerifier)

        async def tool(name, **arguments):
            if name == "search_linkedin_people":
                queries.append(arguments)
                return [] if arguments["location"] else [{"id": 42}]
            return genuine

        verifier.tool = tool
        profiles = await verifier.find_profiles(claims)
        self.assertEqual(profiles[0]["id"], 42)
        self.assertEqual(queries[0]["location"], "Test City")
        self.assertIsNone(queries[1]["location"])

    async def test_facebook_nickname_uses_legal_name_and_separate_id(self):
        _, profile, _ = fixture()
        verifier = object.__new__(CVVerifier)
        requested = []

        async def tool(name, **arguments):
            if name == "search_facebook_users":
                return [] if arguments["q"] == profile["name"] else [{"id": 900}]
            requested.append(arguments["user_id"])
            return {"id": 900, "display_name": "E. Candidate",
                    "original_name": profile["name"], "city": profile["city"]}

        verifier.tool = tool
        fb = await verifier.facebook(profile)
        self.assertEqual(fb["id"], 900)
        self.assertEqual(requested, [900])


if __name__ == "__main__":
    unittest.main()
