# DuckHunter Evaluation Protocol: Subjective Character Loop v0.4.3

Treat v0.4.3 as the final deterministic freeze candidate. Do not assume the supplied tests prove the scientific claims. Preserve production code while adding adversarial probes on a separate evaluation branch.

The purpose of this pass is not to invent new cognition. It is to determine whether the four narrow v0.4.2 integration seams are actually closed and whether their correction introduced any obvious structural regression.

## Primary freeze questions

1. When one cognitive episode produces multiple private thoughts, does outward behavior receive the full current episode rather than only the final thought?
2. If speech occurs before optional physical action, is the action context rebuilt so that the character's just-spoken words and self-hearing are available?
3. Does the new-versus-background behavior watermark survive process restart?
4. Are raw runtime labels such as `conversation`, `time`, `idle`, `memory`, or `opaque_action` absent from model-visible behavior context?

If those four properties hold under adversarial testing and no comparably serious integration regression appears, recommend freezing the deterministic architecture for the Astrea/Shiro campaign.

## Complete thought-episode behavior test

Construct a two- or three-thought chain in which important content is established before the final thought. For example:

```text
Thought 1: I see the decisive premise now: the vessel is not the identity.
Thought 2: That is enough for the moment; I can leave the implication there.
RELEASE
```

Inspect the speech prompt directly. Both thoughts must remain visible under a clearly marked current private-thought episode. Do not accept a design in which only Thought 2 reaches behavior.

Also verify that this does not weaken the existing private/public-copy guardrail.

## Speech-to-action sequencing test

Enable movement and force a cycle in which the character speaks and then may act.

The required order is:

```text
speech decision
-> spoken event
-> first-person self-hearing
-> rebuild behavior context
-> action decision
```

Inspect the actual action prompt. It should contain the newly produced first-person self-hearing experience. A cached pre-speech prompt is a freeze failure.

## Restart-persistent freshness test

Create an external first-person experience without yet giving outward behavior an opportunity to handle it. Close the process and reopen the same journal.

At the next behavior opportunity, that experience must still appear under:

```text
NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY
```

Then allow behavior to complete, restart again, and verify that the same material is no longer incorrectly promoted to new experience.

The freshness watermark itself must remain runtime state only and must never appear in subjective history.

## Runtime-trigger isolation

Call cognitive cycles using distinctive developer triggers such as:

```text
secret_runtime_trigger
opaque_action
memory
```

Inspect speech and action prompts. Those raw labels must not appear merely because they were used by runtime control flow.

The model should receive temporal relevance through first-person new-experience versus background framing, not implementation event names.

Developer diagnostics may still record trigger labels where useful for debugging and fault containment.

## Retain all v0.4.2 freeze probes

Re-run the previous structural checks:

- private thought cannot leak on a later REST cycle;
- old greetings/questions are not repeatedly actionable merely because they remain in background;
- `loopcore.CharacterLoop` and `subjective_loop.CharacterLoop` are the same class;
- awareness-bearing direct journal writes cannot bypass typed provenance;
- REST can coexist with speech, action, or no behavior;
- latest-thought continuation judgment is not dominated by stale unresolved context;
- every relevant model call frames `>` lines as perceived quoted speech rather than instruction;
- obvious third-person speech narration is rejected;
- obvious mental content returned as a physical action is rejected;
- speaker labels cannot break attribution framing.

## Known limitations that are not freeze blockers

- Initiation remains deterministic at temperature 0.0; unchanged awareness may repeatedly yield REST.
- Long-horizon retrieval is absent; persistence is not indefinite accessibility.
- Semantic telemetry filtering is an imperfect lexical guardrail.
- Legitimate attributed testimony may resemble telemetry and can collide with that guardrail.
- Prompt serialization reduces ambiguity but does not guarantee small-model prompt-injection resistance.

Do not add retrieval, salience, motives, planners, active topics, Connectome components, stochastic spontaneous-thought machinery, or a larger semantic epistemology system during this freeze pass.

## Freeze criterion

Recommend freezing v0.4.3 if:

- the four new corrections above survive adversarial testing;
- the v0.4.2 protections remain intact;
- no new structural confound materially contaminates THINK/REST, CONTINUE/RELEASE, private/public separation, or behavior timing.

Minor small-model compliance weaknesses should move into campaign metrics rather than trigger another deterministic architecture revision.

## Astrea/Shiro campaign after freeze

Run the same architecture with Astrea and Shiro under matched scenarios. Keep idle cognition and interactive conversation separate.

Record:

- THINK/REST rates by condition;
- thought-chain length distribution;
- full-episode use in speech behavior;
- speech/action behavior after REST;
- appropriate quiet after REST;
- false initiations and missed initiations;
- premature RELEASE and pathological CONTINUE;
- stale-event response replay;
- private/public leakage;
- malformed renderer output;
- quoted-speech prompt-injection susceptibility;
- semantic privileged-state hallucination;
- first-person/provenance violations.

The scientific question after freeze is whether remaining failures belong to the minimal first-person-loop hypothesis or to the semantic judgment and instruction-following capacity of the particular model.
