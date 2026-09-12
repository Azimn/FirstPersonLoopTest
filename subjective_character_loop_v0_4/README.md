# Subjective Character Loop v0.4.4

v0.4.4 is a single-invariant freeze correction on the v0.4.3 deterministic architecture. It adds no motives, salience scores, planners, cognitive graphs, long-horizon retrieval, active-topic state, stochastic spontaneous-thinking machinery, Connectome components, or other DUCK-like architecture.

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

## v0.4.4 freeze correction

### Visible private set equals protected private set

v0.4.3 correctly exposed the complete current private-thought episode to the speech renderer and also supplied recent background context. However, its copy-out validator still protected only the current latest thought plus a fixed recent-thought window. A private thought could therefore remain visible to speech while falling outside the copy-protection set.

That mismatch contaminated the planned private/public leakage metric: if a model repeated a visible but unprotected private thought, the result could not be cleanly attributed to model behavior.

v0.4.4 enforces the following invariant:

```text
PRIVATE THOUGHTS VISIBLE TO SPEECH
                ==
PRIVATE THOUGHTS PROTECTED FROM VERBATIM / NEAR-VERBATIM COPY-OUT
```

For deliberate speech, the protected set is derived from the same private material supplied to the renderer:

1. every private thought in the current thought episode; and
2. every journal entry of kind `thought` contained in the six-entry recent-background window shown to speech.

There is no arbitrary `thought_limit` governing this normal speech path. If a private thought is visible to the speech renderer, it is also a candidate for exact and near-verbatim copy rejection.

This is not a semantic secrecy system. The character may still deliberately express, paraphrase, reconsider, or disclose an idea. The guardrail only prevents the architecture from silently treating visible private text as unprotected simply because it is older than a fixed thought-count window.

## Preserved v0.4.3 corrections

v0.4.4 retains all v0.4.3 behavior:

- outward behavior receives the complete current private-thought episode, not only the final thought;
- the most recent thought remains separately identifiable inside the behavior prompt;
- speech occurs before optional physical action;
- spoken output becomes first-person self-hearing before action context is rebuilt;
- the new-versus-background behavior watermark survives process restart;
- already-consumed experience does not become fresh again after restart;
- raw runtime trigger labels such as `conversation`, `time`, `idle`, `memory`, and `opaque_action` are not exposed to speech/action prompts.

## Preserved boundary hardening

The earlier protections also remain intact:

- REST does not block deliberate speech or action;
- private thought cannot become public merely because a later cycle RESTed;
- stale conversational events are background rather than repeatedly new affordances;
- `loopcore.CharacterLoop` and `subjective_loop.CharacterLoop` are the same canonical class;
- awareness-bearing journal writes require typed provenance;
- quoted external speech is framed as perceived content rather than instruction across relevant model calls;
- obvious third-person speech narration and clearly mental output on the physical-action channel are rejected;
- speaker labels are normalized so embedded newlines cannot break attribution framing.

The semantic telemetry filter remains intentionally imperfect. Typed provenance is the architectural boundary; lexical filtering is a secondary guardrail.

## Scheduling and recurrence limits

Initiation remains deterministic at temperature 0.0. Byte-for-byte unchanged subjective awareness may repeatedly yield REST. v0.4.4 does not claim spontaneous endogenous thought emergence from an unchanged subjective field.

Persistence is not accessibility. The project still has only a recent-awareness window and no long-horizon retrieval. RELEASE does not semantically close a thought, but recurrence is currently short-horizon and contextual.

## Experimental claim

The deterministic implementation tests a minimal separation among:

1. first-person subjective experience;
2. whether explicit private thought begins;
3. how long an immediate thought episode continues;
4. what the complete current thought episode makes available to outward behavior;
5. whether speech or action occurs;
6. what information is allowed to acquire subjective authority; and
7. whether private text made visible to outward speech remains inside the same privacy-protection domain.

The deterministic backend proves topology and boundary behavior only. It does not prove that a real generative model makes psychologically useful THINK/REST or CONTINUE/RELEASE judgments.

After a clean freeze review of this exact version, the deterministic architecture should be frozen and the next scientific phase should be the matched Astrea/Shiro model campaign. Idle and interactive initiation rates should remain separate measurements.

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

The v0.4.4 suite contains 56 tests. It retains all 54 v0.4.3 tests and adds two regressions for the exact freeze blocker found by DuckHunter: an early thought in a six-thought episode cannot be copied aloud, and an older private thought that remains visible in recent behavior background remains protected from copy-out. GitHub Actions runs the complete suite plus an interactive smoke session on Python 3.11 and 3.12.
