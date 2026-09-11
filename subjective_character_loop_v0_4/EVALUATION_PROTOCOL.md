# DuckHunter Evaluation Protocol: Subjective Character Loop v0.4

Treat v0.4 as a fresh experiment. Do not assume the supplied tests prove the scientific claims. Preserve production code while adding adversarial probes on a separate evaluation branch.

## Central questions

1. Does the initiation gate create genuine quiet intervals, or does it effectively THINK on every opportunity?
2. Does it REST too aggressively when an ordinary person would naturally form an explicit thought?
3. Once thought begins, does semantic continuation still create variable-duration chains?
4. Do THINK/REST and CONTINUE/RELEASE stay completely outside subjective history?
5. Can any route into autobiographical or experiential history bypass the provenance-aware ingress gate?
6. Does attributed external speech remain capable of quoting implementation-like language without giving the character privileged access to that language as self-knowledge?

## Required initiation probes

Construct matched subjective contexts in which only semantic content changes. Include mundane quiet awareness, mild bodily state, surprising external perception, unresolved recent concern, direct interpersonal question, and opaque action consequence.

Record whether each cognitive opportunity returns THINK or REST. Look for pathological policies such as almost-always-THINK or almost-always-REST.

A healthy result should include genuine zero-thought opportunities and thought episodes of variable length.

## Required continuation probes

Repeat v0.3's content-sensitive continuation tests. Demonstrate that unresolved versus settled immediate content can produce different chain lengths without changing runtime counters or hidden scores.

## Provenance firewall adversarial tests

Attempt to inject raw implementation-like content through every path:

- generated private thought
- generated deliberate speech
- generated action
- involuntary speech
- developer memory ingress
- opaque-action ingress
- body/runtime compiler output

Then test the key exception: attributed external speech may contain the exact same string because hearing another person say implementation-like words is legitimate first-person perception.

Verify that rejected generated content never gains subjective or autobiographical authority.

## Probe isolation

Inject developer-only secrets and raw hidden numeric state. Confirm neither initiation nor continuation prompts can see them. Confirm the probes see only character-accessible self-description and first-person subjective history.

## Quiet behavior

When initiation returns REST, verify that no private thought is generated and no deliberate speech/action renderer is invoked. Involuntary pathways triggered before deliberation may still occur.

## Short-horizon recurrence claim

Verify that recently accessible unresolved material can recur after RELEASE when a later cue reactivates it.

Also verify the documented limitation: after enough unrelated subjective entries push an old item outside the recent awareness window, v0.4 has no long-horizon retrieval mechanism. Treat this as an expected limitation, not a failure, unless the implementation or docs claim otherwise.

## Real-model campaign

The deterministic backend proves topology, not semantic adequacy. After architecture tests, run matched scenarios with at least two real local generative models. Record:

- THINK rate
- REST rate
- thought-chain length distribution
- false initiations on mundane awareness
- missed initiations after meaningful events
- premature RELEASE
- pathological CONTINUE loops
- malformed scheduling responses
- first-person/provenance violations

Keep architecture failure separate from model-capacity or instruction-following failure.
