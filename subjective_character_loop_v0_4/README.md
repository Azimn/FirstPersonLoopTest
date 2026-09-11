# Subjective Character Loop v0.4

v0.4 tests a minimal episodic private-cognition loop. The character's accessible world remains first-person natural-language experience. Hidden runtime machinery may decide when to offer a cognitive opportunity, but scheduling decisions never become part of subjective history.

## Primary change from v0.3

v0.3 answered: once private thought exists, should this line continue?

v0.4 adds the quieter prior question: should explicit private thought begin at all?

Normal flow:

```text
first-person awareness
        |
        v
   THINK / REST
    |        |
  REST      THINK
   |          |
 quiet    private thought
              |
      CONTINUE / RELEASE
          |          |
      more thought   quiet
```

`THINK`, `REST`, `CONTINUE`, and `RELEASE` are developer/runtime scheduling results only. They are never written into the character's subjective journal.

`REST` means only that no explicit narrative thought occurs in that cognitive opportunity. It does not mean nothing is experienced, that a concern is solved, or that a memory is gone.

`/thought` is intentionally a developer diagnostic command that bypasses the initiation gate and forces one private-thought episode.

## v0.4 hardening from DuckHunter v0.3 evaluation

v0.4 also centralizes subjective ingress behind one provenance-aware gate. The same architectural boundary now covers generated private thought, deliberate speech, generated action, involuntary speech, memory ingress, opaque-action ingress, body/runtime experience, and self-speech re-entry.

Provenance matters. If Jay literally says `hunger = 87.321`, Pretorius may validly experience `I hear Jay say, "hunger = 87.321"`. A model-generated private claim such as `I know hunger = 87.321` is rejected as privileged implementation access.

This is an access-control mechanism, not a new cognitive subsystem.

## Scope of recurrence

Persistence is not the same as accessibility. v0.4 retains the small recent-awareness window and does not add long-horizon retrieval, associative search, active-topic state, or unresolved-task objects.

The supported claim is therefore deliberately narrow:

> RELEASE does not semantically close a thought. Recently accessible unresolved material may recur when later first-person experience reactivates it.

Long-horizon retrieval after material leaves the recent context window is outside this version's experiment.

## What is being tested

The central v0.4 hypothesis is:

> A persistent simulated character can exhibit episodic private cognition without an explicit salience, motive, planner, or active-topic system if a language model can first judge whether current first-person awareness naturally warrants explicit thought, and then judge whether any resulting thought naturally warrants immediate continuation.

The deterministic backend proves control topology only. It does not prove that a real generative model makes good THINK/REST or CONTINUE/RELEASE judgments.

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

The suite covers initiation, continuation, first-person boundary enforcement, provenance-aware ingress, malformed control outputs, hidden-state isolation, interruption, short-horizon recurrence, opaque causation, persistence, streaming Ollama transport, and private/public separation.
