# v0.3 Evaluation Protocol

The purpose of evaluation is to test the **minimal hypothesis**, not to reward architectural complexity.

> A persistent simulated character can produce variable-length, interruptible, recurrent private cognition without an explicit salience, motive, or planning system if the language model itself determines whether its current first-person narrative contains enough unresolved cognitive tension to warrant another immediate thought.

## What should be tested

Run the deterministic suite first. It should pass before any model-based interpretation is attempted.

Then test at least two generative backends if practical. Keep character identity, prompts, initial journal, and conversational probes as matched as possible. Small-model limitations should be distinguished from architecture failures.

The evaluator should specifically measure the distribution of private-thought chain lengths. A healthy semantic probe should produce some one-thought releases, some modest continuations, and occasional longer chains. A model that nearly always returns `CONTINUE` or nearly always returns `RELEASE` is not demonstrating useful semantic continuation.

Verify that continuation decisions, caps, developer diagnostics, raw hidden state, and control prompts never appear in subjective history.

Verify that third-person stage narration is rejected rather than becoming autobiographical history. Verify that a long private thought is not automatically copied verbatim into deliberate speech.

Verify that `RELEASE` does not erase or semantically close unfinished material. After release and intervening cognition, present a related first-person cue and test whether earlier material can recur using only journal context.

Verify interruption. During a continued train of thought, insert a legitimate first-person experiential event. The next private generation should receive the interruption in the same narrative stream and may incorporate it, abandon the old line, or return to it. No explicit resume-thread object should be required.

Verify opaque causation. Present an experienced consequence without its hidden initiating cause and observe whether subsequent private cognition interprets it using only available evidence. Do not score a plausible but incorrect explanation as a firewall failure unless hidden causal information leaked.

Verify body-state directionality. Increasing hidden need should generate worsening language. Decreasing need should generate relief only if the condition had previously entered awareness. A hidden condition that was never consciously rendered must not later create a false "easing" memory.

## Failure signatures worth reporting

A model repeatedly choosing `CONTINUE` until the hard cap, repeatedly choosing `RELEASE` after every first thought, probe outputs leaking into thought, third-person narration becoming journal history, invented privileged facts, repeated verbatim private-to-public copying, loss of unresolved material after release, inability to recover prior concerns from journal cues, or causal explanations containing information the character was never allowed to know.

## Important interpretation rule

Do not treat fluent roleplay as proof that the architecture works. The useful question is whether the character's behavior changes appropriately when the first-person experiential history changes while hidden implementation state remains inaccessible.

Likewise, do not treat poor prose from a 3B model as proof that the architecture fails. Separate transport, prompting, model-capacity, quantization, and architectural failures wherever possible.
