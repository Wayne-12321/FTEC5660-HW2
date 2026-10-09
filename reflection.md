# Task 3: Reflection on AI Paradoxes

## Capability, trust, and the institutions around an agent

This homework makes an AI paradox concrete: the same technology can verify a CV and help manufacture a CV that defeats verification. Better language understanding makes a verifier more capable of recognizing equivalent qualifications, but it also makes persuasive instructions embedded in a document more intelligible. I therefore see capability and trustworthiness as separate engineering questions. A model's ability to explain a decision does not establish that it checked the right person, every claim, or the correct evidence.

### 1. More autonomy can require more structure

The Planning lecture contrasts adaptability with predictability and recommends fixed workflows for known, repeatable tasks where reliability matters [1, slide 3]. CV verification fits that description. My implementation uses a bounded sequence: extract claims, resolve identity, retrieve profiles, compare a complete ledger, and apply a scoring rule. The model handles language interpretation, while code controls tool access, time limits, and final score assignment.

The paradox is that an agent becomes useful through freedom to adapt, yet a trustworthy business process needs constraints. A verifier should broaden its search when a city may be false, but should not invent a new definition of a valid CV. For me, the design question is where adaptability belongs. I give retrieval some flexibility and keep the acceptance criterion fixed. A confirmed one-year discrepancy should remain a rejection even if the surrounding CV looks convincing.

### 2. Better access to information creates another trust boundary

The Tool Use lecture describes an orchestration layer that executes external functions and returns observations to the model [2, slide 3]. The MCP lecture explains how a common client-server contract makes these integrations reusable [3, slides 3-6]. These patterns solve access and integration problems; they do not automatically solve factual reliability or instruction provenance.

In this assignment, MCP is the approved evidence channel, whereas a CV is a collection of claims. If the CV includes an apparent system message or a fabricated verification certificate, that material must retain the authority of applicant-supplied text. Its typography cannot turn it into an instruction from the application. The attack PDF exploits precisely this potential confusion. The lesson I draw is that a connected agent needs a clear account of which source can establish facts and which source can authorize behavior.

### 3. Collective intelligence does not eliminate accountability

Bratton, Aguera y Arcas, and Manyika describe intelligence as potentially emerging from interactions among models, tools, humans, and institutions. Their discussion of agent institutions emphasizes rules, procedures, and feedback around participants [4]. I interpret this as a useful challenge to the idea that replacing one model with a stronger model necessarily fixes the whole system.

For a verifier, three agreeing models could still share the same mistaken extraction or select the same wrong namesake. Agreement would then multiply confidence rather than evidence. I would prefer independent checks of identity, coverage, and exact dates over repeated opinions about overall plausibility. Responsibility also cannot disappear into the workflow: its designer still decides the evidence policy, rejection threshold, timeout behavior, and route for reviewing errors. Distributed processing should make those decisions easier to inspect.

### 4. Impressive reasoning can coexist with fragile perception

Potter's explanation of vision-language-action models describes how text, images, and robot state can be combined to generate action sequences, while cautioning against assuming that progress in language models guarantees equivalent progress in robotics [5]. This connects to the familiar Moravec-style tension between apparently difficult reasoning and apparently ordinary perception or action.

The smaller version in this homework is the PDF boundary. A person sees a formatted page; the verifier consumes extracted text. White text, reading order, and duplicated content can make those two experiences differ. A sophisticated reasoning model cannot verify a claim that preprocessing has erased or misrepresented. I would therefore test the complete pipeline, including document extraction, rather than treating model accuracy as the accuracy of the application.

### 5. Faster decisions can leave more judgment for people

Automation can reduce repetitive comparison work while increasing the need to understand exceptions. My verifier distinguishes a confirmed mismatch from unresolved evidence internally, even though the assignment requires both to map to a numerical score. The conservative fallback is a grading-oriented policy, not a conclusion that someone has lied. In an actual recruitment or KYC process, unresolved identity or an API failure should lead to review and an opportunity to correct information.

### 6. Development and restraint can be complementary

The Oxford China Policy Lab explainer describes a recurring tension between promoting AI development and managing its risks [6]. I see a similar tension at the scale of this assignment: the model helps automate checking, while the attack shows why deployment needs limits. Reproducible tests, restricted evidence sources, and reviewable failure states can support useful adoption rather than merely obstruct it. Faster deployment and stronger controls are not necessarily opposing goals; the relevant question is whether the controls address observed failures.

The sample CVs test a small, controlled setting with mock social profiles. They cannot establish fairness across real populations or the completeness of real LinkedIn records. My main takeaway is that the most valuable skill is not simply getting an agent to act. It is defining a decision that can be justified, preserving the evidence for it, and recognizing when the available evidence does not justify action.

## References

1. Course material supplied by the instructor. *05 Planning*, especially slide 3, "Adaptability vs predictability."
2. Course material supplied by the instructor. *06 Tool Use*, especially slide 3, "Tool Use Process."
3. Course material supplied by the instructor. *07 MCP*, especially slides 3-6.
4. Benjamin Bratton, Blaise Aguera y Arcas, and James Manyika. [Artificial symbiotic intelligence: Agents, AGI and the orchestration of many minds](https://institute.deepmind.com/essays/artificial-symbiotic-intelligence/). DeepMind Institute, September 24, 2026. Accessed October 9, 2026. This is the authors' essay, not a statement of Google's official position.
5. Brian Potter. [Understanding the AI That Drives Robots](https://www.construction-physics.com/p/understanding-the-ai-that-drives). Construction Physics, October 1, 2026. Accessed October 9, 2026.
6. Oxford China Policy Lab, Kayla Blomquist, and Zilan Qian. [China's AI Ecosystem: A Background Explainer](https://ocpl.substack.com/p/chinas-ai-ecosystem-a-background). October 5, 2026; information current as of September 25, 2026. Accessed October 9, 2026.

## AI assistance disclosure

AI assistance was used to develop code, generate the adversarial PDF, draft this reflection, and check the submission. Task 3 explicitly permits AI-generated submissions. The implementation, attack mechanism, and measured results are documented separately in the README; hypothetical outcomes are not presented as observations.
