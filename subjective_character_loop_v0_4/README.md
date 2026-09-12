# Subjective Character Loop v0.4.3

v0.4.3 is a narrow freeze-correction release. It does not add motives, salience scores, planners, cognitive graphs, long-horizon retrieval, active-topic state, stochastic spontaneous-thinking machinery, Connectome components, or other DUCK-like architecture.

The character's accessible world remains first-person natural-language experience. Hidden runtime scheduling and boundary-control decisions remain outside subjective history.

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
          |
        speech
          |
   first-person self-hearing
          |
   rebuild present context
          |
   optional physical action
```

`REST` still means only that no explicit private narrative thought occurs. It neither requires nor prevents outward behavior.

## v0.4.3 freeze corrections

### Behavior sees the full current thought episode

v0.4.2 exposed only the final private thought to outward behavior. A chain such as:

```text
Thought 1 -> Thought 2 -> RELEASE
```

could therefore lose information established in Thought 1 before speech was rendered.

v0.4.3 passes the complete current private-thought episode to the behavior renderer. The most recent thought remains identifiable, but earlier thoughts from the same immediate episode are not discarded.

### Action context is rebuilt after speech

Speech is rendered first. If speech occurs, it becomes first-person self-hearing exactly as before. Only then is the action prompt rebuilt.

This means an optional action can respond to what the character actually just said rather than to a stale pre-speech snapshot.

### Behavior freshness survives restart

The watermark separating newly arrived first-person experience from older background is now persisted in runtime state.

If an external perception arrives and the process restarts before outward behavior handles it, that perception remains new after restart. Conversely, already-handled material does not become fresh again merely because the process restarted.

This watermark remains runtime bookkeeping. It is never part of the character's subjective experience.

### Raw runtime trigger is not model-visible

Labels such as `conversation`, `time`, `idle`, `memory`, or `opaque_action` remain available for developer diagnostics where useful, but they are not included in the behavior model's prompt.

Behavior instead receives only the first-person temporal frame:

```text
NEW FIRST-PERSON EXPERIENCE SINCE THE PREVIOUS BEHAVIOR OPPORTUNITY
CURRENT PRIVATE THOUGHT EPISODE
MOST RECENT PRIVATE THOUGHT FROM THIS CYCLE
RECENT BACKGROUND
```

This avoids giving the model implementation-level event labels merely to communicate temporal relevance.

## Preserved v0.4.2 hardening

v0.4.3 retains the previous protections:

- recent private thought cannot be copied verbatim into later speech simply because the current cycle RESTed;
- stale conversational events are background rather than repeatedly new affordances;
- `loopcore.CharacterLoop` and `subjective_loop.CharacterLoop` are the same canonical class;
- awareness-bearing journal writes require typed provenance;
- quoted external speech is framed as perceived content rather than instruction across all relevant model calls;
- obvious third-person speech narration and clearly mental output on the physical-action channel are rejected;
- speaker labels are normalized so embedded newlines cannot break attribution framing.

The semantic telemetry filter remains intentionally imperfect. Typed provenance is the architectural boundary; lexical filtering is only a guardrail.

## Scheduling and recurrence limits

Initiation remains deterministic at temperature 0.0. Byte-for-byte unchanged subjective awareness may repeatedly yield REST. v0.4.3 does not claim spontaneous endogenous thought emergence from an unchanged subjective field.

Persistence is not accessibility. The project still has only a recent-awareness window and no long-horizon retrieval. RELEASE does not semantically close a thought, but recurrence is currently short-horizon and contextual.

## Experimental claim

The deterministic implementation tests a minimal separation among:

1. first-person subjective experience,
2. whether explicit private thought begins,
3. how long an immediate thought episode continues,
4. what the complete current thought episode makes available to outward behavior,
5. whether speech or action occurs,
6. what information is allowed to acquire subjective authority.

The deterministic backend proves topology and boundary behavior only. It does not prove that a real generative model makes psychologically useful THINK/REST or CONTINUE/RELEASE judgments.

After a clean freeze review, the next scientific phase is a matched Astrea/Shiro model campaign. Idle and interactive initiation rates should remain separate measurements.

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

The v0.4.3 suite contains 54 tests. It retains the complete v0.4.2 suite and adds regressions proving that behavior receives the full current thought episode, action context is rebuilt after speech/self-hearing, the behavior freshness watermark survives restart, and raw runtime trigger labels do not enter model-visible behavior context. GitHub Actions runs the complete suite plus an interactive smoke session on Python 3.11 and 3.12.
