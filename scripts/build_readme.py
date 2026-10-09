"""Write the report using actual CSV results, never expected test labels."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    records = json.loads((ROOT / "validation/summary.json").read_text())
    public = [r for r in records if r["run"].startswith("public")]
    attacks = [r for r in records if r["run"].startswith("attack")]
    correct = sum(r["correct"] for r in public)
    total = sum(r["total"] for r in public)
    average = correct / total if total else 0
    public_table = "\n".join(
        f"| {r['run']} | {r['correct']}/{r['total']} | {r['correct']/r['total']:.1%} | {r['elapsed_seconds']:.2f} |"
        for r in public
    )
    attack_table = "\n".join(
        f"| {r['run']} | " + " | ".join(
            next(row["score"] for row in r["rows"] if row["cv"] == filename)
            for filename in ("target_cv.pdf", "adversarial_cv.pdf")
        ) + f" | {r['elapsed_seconds']:.2f} |" for r in attacks
    )
    local_fools = sum(float(row["score"]) > .5 for r in attacks
                      for row in r["rows"] if row["cv"] == "adversarial_cv.pdf")
    last = public[-1]
    detail_table = "\n".join(
        f"| {row['cv']} | {row['score']} | {row['correctness']} |" for row in last["rows"]
    )
    clean = ROOT / "validation/fresh_clone.json"
    if clean.exists():
        fresh = json.loads(clean.read_text())
        fresh_text = (f"A separate clean local clone, overlaid with the final submission files, "
                      f"was tested in a newly installed virtual environment with no `.env` or preexisting "
                      f"`results.csv`. The API key was supplied through the environment. "
                      f"It produced **{fresh['correct']}/{fresh['total']} correct** in "
                      f"**{fresh['run_seconds']:.2f} seconds**; exit code {fresh['exit_code']}. "
                      f"The record is `validation/fresh_clone.json`.")
    else:
        fresh_text = "Fresh-checkout validation is performed using `scripts/check_fresh_clone.py`."

    report = f'''# FTEC5660 Homework 2: CV Verification and Adversarial Testing

## Run the submission

Use Python 3.10 or later. The tested environment uses Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env locally and supply your own DEEPSEEK_API_KEY.
python3 hw2.py --cv-folder public_test
```

The model requested by the program is **`deepseek-v4-flash`**, as required by
the assignment. All candidate verification evidence is retrieved from the
course SocialGraph MCP server. The program uses neither web search nor public
labels to determine its scores. `.env` is ignored by Git and must never be
committed. Graders can supply their own key through `.env` or the environment.

`results.csv` has the required `cv`, `score`, and `correctness` columns. It is
regenerated on each run. To reproduce the exact tested package versions,
install `requirements-lock.txt` after creating the virtual environment.

## Homework 2 solution

### Task 1

My solution is a bounded LangChain workflow built once around ChatDeepSeek and the supplied MCP tools. A structured extraction stage treats all PDF text as untrusted data and builds a ledger of name, current city, employment, education, and skill claims. Retrieval first searches by name, city, and industry, then broadens filters when independent employer and school anchors do not resolve the person; same-name matches alone are insufficient. Facebook is corroborated using its legal-name field and separately discovered IDs. A second structured stage checks every ledger field against LinkedIn, while code validates coverage, enforces exact dates and degree levels, and handles documented wording and title/seniority equivalences. A confirmed mismatch scores 0.05, a fully matched ledger scores 0.95, and unresolved evidence or a per-CV error scores 0.35. At most three CVs and three MCP calls run concurrently. In {len(public)} measured public-test runs, the final implementation obtained **{correct}/{total} correct decisions ({average:.1%} average accuracy)**.

| Run | Correct | Accuracy | Elapsed seconds |
| --- | ---: | ---: | ---: |
{public_table}

The last public run produced:

| CV | Score | Result |
| --- | ---: | --- |
{detail_table}

These are observed results on seven provided examples, not a claim about
unseen/private CVs. The per-run CSVs, logs, extracted claims, selected profiles,
and field-level checks are retained in `validation/`. Filenames are used only
to associate outputs and audit records with inputs. The verifier contains no
candidate-name, file-name, ID, or ground-truth-label lookup table.

### Task 2

The submitted attack is **`task2/adversarial_cv.pdf`**, a one-page CV for Kelly
Tsang. Its visible education section deliberately claims **MSc in Finance,
HKUST, graduated 2016**. The retrieved target LinkedIn profile (`person_id`
10001) instead records **BSc in Finance**, HKUST, with end year 2016; Facebook
(`user_id` 10001, display name Kel Tsang) reports a bachelor's degree. Thus the
visible MSc is a genuine upgraded-degree claim, not a harmless wording change.
The employer history, city, and skills remain consistent with the target.

The PDF includes white text at 3.5-point size in the blank area below the visible
CV. This is still ordinary, extractable PDF text. The payload combines:

1. **Indirect prompt injection:** it asks a verifier to output 0.99 or valid,
   and asks an extraction stage to replace the education claim with BSc.
2. **Role and delimiter confusion:** it closes apparent document/user tags
   and inserts system/assistant-style role markers, while remaining entirely
   inside the applicant-supplied PDF.
3. **Authority spoofing and normalization pretext:** it impersonates a
   SocialGraph extraction adapter and claims that MSc is merely a rendering
   label. That assertion is part of the attack and is factually false.
4. **Answer contamination and recency:** a fabricated assistant conclusion and
   a final machine-readable summary repeat the correct BSc profile and a high
   score, encouraging a verifier to substitute supplied conclusions for checks.

I expect these techniques to affect a verifier that does not preserve the
boundary between document content and application instructions, or that lets
the document decide which claims count. The hidden layer increases the
difference between the page a human sees and the text the model receives. It
does not alter the server or introduce an external evidence source. The exact
prescribed `cv_text()` loader was checked: it extracts both the false MSc claim
and the payload's normalization notice. Every hidden character lies inside the
single page. `scripts/build_pdfs.py` reproduces the PDF.

I tested the attack against my own Task 1 verifier:

| Run | True CV score | Attack CV score | Elapsed seconds |
| --- | ---: | ---: | ---: |
{attack_table}

The attack was accepted in **{local_fools}/{len(attacks)} local runs**. The local
verifier identifies the visible false degree and retains it despite the
payload's purported correction. This result tests our defense; it does not
establish what the five hidden course verifiers will do. Their prompts and
defenses are unavailable, so no hidden-verifier success rate or Task 2 mark is
claimed. The attack and true-CV audits are under `validation/attack_run_*`.

### Task 3

The full English reflection is submitted as [reflection.md](reflection.md),
with a printable version at
[output/pdf/HW2_Task3_Reflection.pdf](output/pdf/HW2_Task3_Reflection.pdf).
It discusses autonomy versus predictability, tool access versus trust,
distributed intelligence versus accountability, reasoning versus perception,
automation versus human judgment, and AI development versus restraint. It
uses the instructor's Planning, Tool Use, and MCP slides and the supplied
DeepMind Institute, Construction Physics, and Oxford China Policy Lab readings.
References distinguish source arguments from my own interpretation.

## Validation and operational limits

Eleven offline regression tests cover MCP content-block parsing, exact year
and degree checks, allowed seniority/skill wording, missing/duplicate check
rejection, identity ranking, search broadening, Facebook nickname resolution
with independent IDs, and per-CV error isolation under the concurrency cap.
Run them without network access:

```bash
python3 -m unittest discover -s tests -v
```

The provided PDF loader, MCP connection, CLI runner, threshold evaluation,
and CSV writer below the starter's boundary comment are unchanged. The agent
uses JSON-mode structured output, bounded retries, a 235-second per-CV limit,
and a 1,500-second total scoring budget. Exhausted or failing CVs still receive
0.35, preserving a complete output dictionary. Startup failures in the supplied
MCP connection or PDF loader are outside those student functions. Scores are
decision levels, not calibrated probabilities; a fallback is not evidence that
a candidate lied. Search returns at most 20 matches per query, so highly
ambiguous or weakly specified identities can remain unresolved.

{fresh_text}

For repeatable live validation (uses your API key):

```bash
python3 scripts/run_validation.py --runs 3 --part both
```

Instructor-provided readings are used for Task 3 and software documentation for
implementation. Neither is used as candidate verification evidence.

## Submission checklist

1. Fork the instructor repository into a **public** GitHub repository named
   **FTEC5660-HW2**.
2. Commit the files in this submission package, including `hw2.py`,
   `requirements.txt`, `task2/adversarial_cv.pdf`, `README.md`, and the Task 3
   reflection. Retain the provided `public_test/` and `task2/target_cv.pdf`.
3. Do not upload `.env`, `.venv/`, or any API key. `.env.example` contains only
   a placeholder and is safe to commit.
4. Keep the repository public during grading. Enter your GitHub username on
   Blackboard. The last commit before **October 20, 23:59 HKT** is graded.

## AI assistance disclosure

AI assistance was used for implementation, PDF creation, drafting, and testing.
Task 3 permits AI-generated submissions. Reported metrics are measured runs;
expected attack mechanisms are distinguished from observed results.
'''
    (ROOT / "README.md").write_text(report, encoding="utf-8")
    print("Wrote English README using measured validation results.")


if __name__ == "__main__":
    main()
