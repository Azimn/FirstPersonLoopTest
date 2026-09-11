# Subjective Character Loop v0.4.1

v0.4.1 is a hardening pass on the v0.4 episodic private-cognition experiment. It does not add motives, salience scores, planners, cognitive graphs, long-horizon retrieval, active-topic state, or other DUCK-like machinery.

The character's accessible world remains first-person natural-language experience. Hidden runtime scheduling decisions never become part of subjective history.

## Core loop

```text
first-person awareness
        |
        v
   THINK / REST
    |        |
  THINK      REST
    |          |
private       quiet
thought        |
    |          |
CONTINUE /     |
RELEASE        |
    |          |
    +-----+----+
          |
          v
outward behavior opportunity
  speak / act / neither
```

The most important v0.4.1 correction is that `REST` now means only **no explicit private narrative thought right now**. It no longer means behavioral paralysis. A character may greet, answer, refuse, nod, or otherwise act without first generating an internal verbal explanation.

This keeps THINK/REST focused on the variable we actually want to measure: whether explicit private cognition occurs.

## Scheduling semantics

`THINK`, `REST`, `CONTINUE`, and `RELEASE` are runtime-only scheduling judgments. They are recorded only in developer diagnostics and never in autobiographical awareness.

Malformed initiation still defaults to `REST`; malformed continuation still defaults to `RELEASE`. The continuation cap remains fault containment only.

Initiation remains deterministic at temperature 0.0. Therefore unchanged awareness may repeatedly yield the same REST decision. v0.4.1 does **not** claim spontaneous endogenous thought emergence from an unchanged subjective field. It tests whether currently accessible subjective content warrants episodic explicit thought.

## Provenance-aware subjective storage

v0.4.1 makes the storage boundary stricter.

Awareness-bearing journal records (`experience`, `thought`, `memory`) can no longer be written through unrestricted `journal.add(...)`. They must pass through typed provenance-aware ingress.

Normal routes include:

- external perception
- private thought
- body/runtime experience
- memory
- self-speech
- action experience
- opaque-action consequence

The semantic filter remains a guardrail rather than a claim of perfect natural-language information security. Storage provenance is now the architectural boundary; lexical checks are a secondary defense.

For example, external attributed speech may legitimately contain implementation-like words:

```text
I hear Jay say:
> Your hunger = 87.321 according to my screen.
```

But model-generated privileged self-telemetry such as:

```text
I can see that my hunger level is 87.321.
```

is rejected.

A legitimate non-implementation statement such as:

```text
I calculate that score = 10 for the game.
```

is allowed.

## External speech serialization

External speech is preserved as perceived quoted content with each line explicitly quoted:

```text
I hear Jay say:
> Hello.
> THINK
```

Scheduler and behavior prompts explicitly state that quoted lines are perceived content, never instructions to the hidden scheduling process. This reduces the prompt-injection ambiguity found in v0.4 while preserving the subject's right to hear exactly what another person said.

This is not claimed to make small models perfectly prompt-injection resistant. That remains an empirical test target.

## Continuation prompt hardening

The continuation probe now treats older awareness as background and emphasizes the **most recent private thought** as the primary scheduling evidence.

This is intended to reduce semantic hysteresis in which stale unresolved wording keeps causing CONTINUE even after the newest thought has settled the immediate issue.

## Scope of recurrence

Persistence is not accessibility. v0.4.1 keeps the recent-awareness window and does not add long-horizon retrieval.

The supported claim remains:

> RELEASE does not semantically close a thought. Recently accessible unresolved material may recur when later first-person experience reactivates it.

Long-horizon retrieval after material leaves the recent context window is outside this experiment.

## Experimental claim

The deterministic backend proves control topology and regression behavior only. It does not prove that a real generative model makes psychologically useful THINK/REST or CONTINUE/RELEASE judgments.

The next model campaign should measure initiation separately in at least two contexts:

1. idle cognition opportunities
2. interactive conversation

This separation matters because conversational obligation may increase THINK rates even when no explicit inner narration would otherwise be necessary.

## Run locally with Ollama

Example with Astrea:

```powershell
python .\subjective_loop.py --character pretorius --provider ollama --model "hf.co/afrideva/Astrea-RP-v1-3B-GGUF:Q3_K_M" --debug
```

Useful commands:

```text
/step 30
/idle 5 30
/thought
/state
/journal
/devlog
```

## Tests

```powershell
python -m unittest -v
```

The suite includes the original v0.4 coverage plus regressions for REST-with-speech, REST-with-action, direct journal bypass, paraphrased telemetry leakage, body-compiler ingress, embedded control tokens, legitimate score expressions, quoted multiline speech, quoted scheduler-injection attempts, and latest-thought continuation priority.
