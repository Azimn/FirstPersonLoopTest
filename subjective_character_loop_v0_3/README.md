# Subjective Character Loop v0.3

v0.3 is a deliberately small experiment in persistent first-person cognition.

The character-facing world is natural-language experience only. Hidden runtime values may exist, but they are translated before they can enter awareness. Heard speech is experienced as heard speech, bodily state as sensation, memory as recollection, action as experienced action, and model-generated cognition as private thought.

The central change from v0.2 is **emergent thought duration**. The runtime no longer decides in advance that a cycle will contain a fixed or random number of private generations. It generates one private thought, then asks a separate hidden semantic probe whether another immediate thought naturally follows. The probe may return only `CONTINUE` or `RELEASE`. That control result is developer-only scheduling information and is never stored in the subjective journal.

`RELEASE` means only that attention rests for now. It does not mark a concern solved, closed, forgotten, or completed. Later experiences can naturally bring prior material back because earlier first-person thoughts remain in the journal.

## Core loop

```text
first-person experience
        ↓
private thought
        ↓
hidden continuation probe
   CONTINUE / RELEASE
        ↓         ↓
 private thought  quiet
        ↓
      probe...
```

A configurable hard continuation cap exists only as fault containment against a model that refuses to release. Hitting the cap creates a developer diagnostic, not a subjective experience.

## First-person boundary

Examples of character-facing input:

```text
I hear Jay say, "What are you working on?"
I'm getting hungry.
I remember Jay asking me about this earlier.
I find myself standing beside the table.
Why does that bother me so much?
```

Examples that must not enter awareness:

```text
hunger = 87.3
interest_score = 0.71
CONTINUE
RELEASE
continuation_count = 4
memory_id = 188
```

The architecture also permits **opaque causation**. A hidden process may cause an action while the character receives only the first-person consequence, such as `I find myself standing beside the table.` The system does not inject a causal explanation merely to make introspection correct.

## Running locally with Ollama

From this directory on Windows PowerShell:

```powershell
python .\subjective_loop.py --character pretorius --provider ollama --model "hf.co/afrideva/Astrea-RP-v1-3B-GGUF:Q3_K_M" --thought-tokens 180 --speech-tokens 80 --max-continuations 12
```

Alternative small roleplay model:

```powershell
python .\subjective_loop.py --character pretorius --provider ollama --model "hf.co/samunder12/Llama-3.2-3B-small_Shiro_roleplay-gguf:Q4_K_M" --thought-tokens 180 --speech-tokens 80 --max-continuations 12
```

Use `--debug` to display developer-only continuation decisions. Without `--debug`, `CONTINUE` and `RELEASE` remain invisible in the interactive transcript.

Useful console commands:

```text
/step 30
/idle 3 30
/thought
/body hunger 90
/interest 90 synthetic life
/pain 90
/opaque standing beside the table
/remember Jay asking me about the experiment this morning
/journal
/devlog
```

## Model-free architecture test

```powershell
python .\subjective_loop.py --character pretorius --provider scripted --debug
```

The deterministic backend deliberately produces variable cycle lengths, speech, and silence. It exists to test the shell, not character quality.

## Tests

```powershell
python -m unittest -v
```

The v0.3 suite checks semantic release/continuation, variable cycle length, malformed probe fallback, fault containment, probe isolation, hidden-state leakage, first-person transformation, interruption between thoughts, recurrence after release, opaque causation, persistence, directional body-state rendering, private/public separation, and streamed Ollama transport.

See [EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) for the DuckHunter handoff and [RESEARCH_RATIONALE.md](RESEARCH_RATIONALE.md) for the evidence trail behind major design decisions.
