# Subjective Character Loop v0.1

This is a deliberately small experimental runtime for testing a single idea: the character never receives raw simulation state. Every character-accessible input is first-person natural-language experience. Hidden state exists only in the runtime.

The prototype separates private inner thought from intentional speech. It also contains a minimal optional physical-action channel and a sudden-pain path that can cause an involuntary vocalization. Hunger, fatigue, pain, temperature discomfort, boredom, and positive interest/engagement are hidden numerical variables. Threshold crossings and high-intensity recurrence produce first-person awareness such as "I'm really hungry" or "I can't stop thinking about this experiment." The character never sees the number that caused the sentence.

The default profile is Dr. Septimus Pretorius. A conservative Kiki profile is included as a second comparison character so the same engine can later be tested for identity leakage and voice homogenization.

## Running with Ollama

The program uses only the Python standard library. Start Ollama locally, make sure the desired model is installed, then run:

```bash
python subjective_loop.py --character pretorius --provider ollama --model qwen3:8b
```

The database is persistent. By default it is created in the current directory as `pretorius_subjective_loop.sqlite3`.

Ordinary text is treated as something the character hears. Developer controls are available through `/help`. For example, this raises interest in a topic without exposing the numerical value to the character:

```text
/interest 90 a new method for creating synthetic life
```

This advances simulated time and allows hidden hunger, fatigue, boredom, interest, pain, and temperature state to change:

```text
/wait 600
```

This creates a sudden pain event and may cause a brief involuntary spoken reaction before reflective thought:

```text
/pain 85
```

The `/state` command is strictly a developer view. Its values are never included in character prompts.

## Architectural test mode

The scripted backend does not attempt to imitate a real character. It exists only so the control flow can be tested without a model:

```bash
python subjective_loop.py --character pretorius --provider scripted --seed 7
python -m unittest -v test_subjective_loop.py
```

## Current boundary

The runtime does not yet contain a world simulator. Incoming speech is treated as directly heard, and physical actions are only logged if the optional movement channel is enabled. This is intentional. Version 0.1 isolates the subjective loop before perception, spatial simulation, relationships, graph memory, or other cognitive machinery are introduced.
