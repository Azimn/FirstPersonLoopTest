# iPhone Test Harness for Subjective Character Loop v0.4.4

This mobile harness does not move the model or cognitive architecture onto the iPhone. The frozen Subjective Character Loop v0.4.4, SQLite journal, and Ollama model continue running on the Windows PC. Safari on the iPhone is a thin research interface over the local Wi-Fi network.

That separation is intentional. It lets the phone test real Astrea or Shiro behavior without creating a second mobile-specific implementation of the experiment.

## Requirements

- Windows PC and iPhone connected to the same Wi-Fi network.
- Ollama running on the Windows PC.
- The desired Ollama model already installed.
- Python 3.11 or 3.12 on Windows.
- No port forwarding. This test server is intended for the local network only.

## Get the mobile-test branch

From PowerShell:

```powershell
git clone -b v0.4.4-iphone-mobile-test https://github.com/Azimn/FirstPersonLoopTest.git
cd .\FirstPersonLoopTest\subjective_character_loop_v0_4
```

If the repository is already cloned:

```powershell
git fetch origin
git switch v0.4.4-iphone-mobile-test
cd .\subjective_character_loop_v0_4
```

## Start Pretorius with Astrea

```powershell
python .\mobile_server.py --character pretorius --provider ollama --model "hf.co/afrideva/Astrea-RP-v1-3B-GGUF:Q3_K_M" --thought-tokens 180 --speech-tokens 80 --max-continuations 12
```

The server prints two addresses. The important one looks similar to:

```text
iPhone on same Wi-Fi: http://192.168.1.25:8765
```

Leave that PowerShell window open.

The first time Python listens on the network, Windows Firewall may ask for permission. Allow access on **Private networks**. Public-network access is not needed.

## Open it on the iPhone

Open Safari and enter the `http://...:8765` address printed by the server.

The mobile interface shows private thought, first-person experience, outward speech, memory, and action as distinct transcript types. This is a researcher view. It is deliberately not limited to what the character publicly says.

The quick controls provide an idle 30-second opportunity, an idle 5-minute opportunity, a forced private-thought diagnostic, and a hunger injection. The Research Controls drawer also exposes body channels and interest so simple matched scenarios can be run from the phone.

Safari can also use **Share > Add to Home Screen** for a more app-like launch surface. The local test remains dependent on the Windows server being running and reachable.

## Start Shiro instead

```powershell
python .\mobile_server.py --character pretorius --provider ollama --model "hf.co/samunder12/Llama-3.2-3B-small_Shiro_roleplay-gguf:Q4_K_M" --thought-tokens 180 --speech-tokens 80 --max-continuations 12
```

Use a separate database if you want the Astrea and Shiro histories completely isolated:

```powershell
python .\mobile_server.py --character pretorius --provider ollama --model "hf.co/afrideva/Astrea-RP-v1-3B-GGUF:Q3_K_M" --db .\pretorius_astrea_mobile.sqlite3
```

and:

```powershell
python .\mobile_server.py --character pretorius --provider ollama --model "hf.co/samunder12/Llama-3.2-3B-small_Shiro_roleplay-gguf:Q4_K_M" --db .\pretorius_shiro_mobile.sqlite3
```

## Architecture rule

`mobile_server.py` is only an adapter. Messages from Safari call the same `CharacterLoop` methods used by the command-line version. No mobile-specific THINK/REST logic, continuation logic, memory system, prompt, persona, or subjective-ingress rule is introduced.

The mobile branch should therefore be treated as a user-interface experiment around the frozen v0.4.4 architecture, not as v0.4.5.
