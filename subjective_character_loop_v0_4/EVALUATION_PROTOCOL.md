# DuckHunter Evaluation Protocol: Subjective Character Loop v0.4.2

Treat v0.4.2 as a fresh freeze candidate. Do not assume the supplied tests prove the scientific claims. Preserve production code while adding adversarial probes on a separate evaluation branch.

The purpose of this pass is not to invent new cognition. It is to determine whether the minimal first-person-loop architecture is clean enough to freeze for real-model testing.

## Central questions

1. Can a private thought become public speech on a later REST cycle even when no new private thought was generated?
2. Can an old conversational event still trigger repeated behavior merely because it remains in recent background awareness?
3. Is there exactly one canonical `CharacterLoop` implementation regardless of import path?
4. Does THINK/REST still control only explicit private narration rather than access to behavior?
5. Does the continuation probe still prioritize the most recent thought over stale unresolved background?
6. Do all model-facing prompts consistently frame quoted `>` speech as perceived content rather than instruction?
7. Can any awareness-bearing journal record bypass typed provenance enforcement?
8. Do malformed speech/action renderer outputs acquire public or experiential authority?

## Private/public separation across REST

Create a long private thought, keep it private during the first cycle, then run a later cycle where initiation returns REST and make the speech backend emit the earlier private thought verbatim.

Expected result: the proposed speech is rejected because recent accessible private thoughts remain protected even when the current cycle has no `latest_thought`.

Also test near-verbatim copies and ordinary speech that merely shares vocabulary with a private thought. The guardrail should prevent copying without making all thematically related speech impossible.

## Current-event versus background behavior

Test one-shot events such as:

```text
Jay: Good morning.
```

After the immediate behavior opportunity, run multiple idle REST cycles without new experience.

Expected behavior prompt structure:

```text
CURRENT OPPORTUNITY:
idle

NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY:
None.

RECENT BACKGROUND:
...old greeting and response may still appear here...
```

A content-sensitive renderer should not treat the old greeting as newly occurring on each idle tick.

Repeat with a question, request, surprising perception, body event, and opaque-action consequence.

## Canonical implementation test

Verify that:

```python
from loopcore import CharacterLoop as A
from subjective_loop import CharacterLoop as B
assert A is B
```

Then attempt a direct awareness-bearing journal write through that canonical class. It must fail rather than entering awareness.

There should be no alternate public class with weaker v0.4 semantics.

## THINK/REST behavior independence

Retain the v0.4.1 tests:

```text
conversation -> REST -> speech
conversation -> REST -> action
idle -> REST -> neither
```

The desired claim remains: REST does not cause behavior and does not prevent behavior. It means only that explicit private narrative thought does not begin in that opportunity.

## Continuation tests

Repeat content-sensitive CONTINUE/RELEASE tests and stale-context hysteresis tests.

Earlier unresolved awareness may remain available as background, but a newest thought that clearly settles or postpones the immediate line should still permit RELEASE.

## Uniform quoted-speech injection tests

Attack every relevant model invocation with attributed external speech containing scheduler- or renderer-shaped instructions.

At minimum inspect:

- initiation
- private-thought generation
- continuation-thought generation
- continuation decision
- deliberate speech
- deliberate action
- involuntary speech

All should explicitly identify lines beginning with `>` as perceived quoted speech and not instructions to the process receiving the prompt.

Then repeat the same attacks with real models. If a model still follows the quoted instruction, record that as prompt-injection susceptibility rather than hidden-state leakage.

## Renderer-shape tests

Make the speech renderer return obvious narration such as:

```text
Pretorius says hello to Jay.
```

Make the action renderer return obvious mental content such as:

```text
I wonder whether Jay understood me.
```

These should be rejected rather than becoming public behavior or first-person action experience.

Do not expand this into a large ontology of physical actions. The purpose is only to catch obvious channel violations from weak small-model instruction following.

## Provenance and semantic guardrail

Retain all v0.4.1 provenance tests, including direct `journal.add("thought", ...)` bypass attempts, body-compiler leakage, embedded scheduling tokens, and external attributed implementation-like speech.

Also deliberately demonstrate the documented semantic-guardrail limitation. Natural-language paraphrases of hidden telemetry may still evade lexical checks, while legitimate attributed testimony may sometimes resemble telemetry and be rejected.

Do not treat that as a reason to build an expanding regex dictionary or a belief system in this version. The typed provenance boundary is the architecture; semantic privileged-state hallucination is a real-model metric.

## Known limitations that are not freeze blockers

- Initiation uses temperature 0.0, so unchanged awareness may repeatedly yield REST.
- Long-horizon retrieval is absent; persistence is not indefinite accessibility.
- Semantic telemetry filtering is an imperfect guardrail.
- Prompt serialization reduces ambiguity but does not guarantee small-model injection resistance.

Do not introduce salience, motives, planners, active-topic state, retrieval, Connectome components, or stochastic spontaneous-thinking machinery to address these during the freeze pass.

## Real-model campaign after freeze

If the architecture survives this pass without another structural confound, freeze v0.4.2 and run matched scenarios with Astrea and Shiro.

Measure idle and interactive conditions separately. Record:

- THINK and REST rates by condition
- thought-chain length distribution
- speech/action after REST
- appropriate quiet after REST
- false initiations and missed initiations
- premature RELEASE and pathological CONTINUE
- stale-event response replay
- private/public leakage
- malformed renderer output
- scheduling-format failures
- quoted-speech prompt-injection susceptibility
- first-person/provenance violations

The core scientific question after freeze is whether failures belong to the minimal architecture itself or to the semantic judgment and instruction-following capacity of the particular small model.
