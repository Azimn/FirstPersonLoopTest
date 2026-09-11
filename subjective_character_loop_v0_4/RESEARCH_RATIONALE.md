# Research Rationale and Source Trail: v0.4

This file preserves the evidence trail for design decisions. The sources motivate experiments; they do not establish machine consciousness or prove that this architecture reproduces human cognition.

## First-person verbal cognition and inner speech

The project represents character-accessible explicit cognition in first-person natural language while keeping implementation state outside awareness. This is informed by work treating inner speech as a functionally varied component of human cognition, without assuming that all human cognition is verbal.

Alderson-Day, B., & Fernyhough, C. (2015). *Inner Speech: Development, Cognitive Functions, Phenomenology, and Neurobiology*. Psychological Bulletin, 141(5), 931–965. https://doi.org/10.1037/bul0000021

## Spontaneous thought and current concerns

v0.4's THINK/REST gate tests whether explicit thought can occur episodically rather than on every runtime tick. This is an engineering hypothesis inspired by evidence that spontaneous thought varies with ongoing concerns and context. The source does not imply a biological binary gate.

Mildner, J. N., & Tamir, D. I. (2024). *Why do we think? The dynamics of spontaneous thought reveal its functions*. PNAS Nexus, 3(6), pgae230. https://doi.org/10.1093/pnasnexus/pgae230

## Unfinished material and continued cognition

The CONTINUE/RELEASE probe tests unresolved cognitive tension semantically before adding numeric salience machinery.

Wendsche, J., Weigelt, O., & Syrek, C. J. (2026). *Unfinished work tasks and work-related thoughts during off-job time: meta-analysis of the Zeigarnik effect in a work-recovery context*. Anxiety, Stress, & Coping, 39(4), 385–407. https://doi.org/10.1080/10615806.2026.2616302

## Limited introspective access and post-hoc explanation

The architecture permits experienced consequences whose hidden causes are unavailable to the character. Subsequent first-person cognition may infer or rationalize those causes from accessible evidence.

Nisbett, R. E., & Wilson, T. D. (1977). *Telling more than we can know: Verbal reports on mental processes*. Psychological Review, 84(3), 231–259. https://doi.org/10.1037/0033-295X.84.3.231

Gazzaniga, M. S., Eliassen, J. C., Nisenson, L., Wessinger, C. M., Fendrich, R., & Baynes, K. (1996). *Collaboration between the hemispheres of a callosotomy patient: Emerging right hemisphere speech and the left hemisphere interpreter*. Brain, 119(4), 1255–1262. https://doi.org/10.1093/brain/119.4.1255

Volz, L. J., & Gazzaniga, M. S. (2017). *Interaction in isolation: 50 years of insights from split-brain research*. Brain, 140(7), 2051–2060. https://doi.org/10.1093/brain/awx139

## Split-brain caution

Split-brain findings motivate separating information access, action control, report, and interpretation. They should not be simplified into a claim that split-brain patients contain two clean independent persons.

de Haan, E. H. F., et al. (2020). *Split-Brain: What We Know Now and Why This is Important for Understanding Consciousness*. Neuropsychology Review, 30(2), 224–233. https://doi.org/10.1007/s11065-020-09439-3

## Natural-language agent memory as engineering precedent

Park et al. provide precedent for persistent natural-language agent experience. Subjective Character Loop deliberately does not import their planning, reflection scoring, or retrieval architecture at this stage.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*. UIST 2023. https://doi.org/10.1145/3586183.3606763

## v0.4 evidence discipline

DuckHunter's v0.3 evaluation demonstrated that persistence in SQLite is not equivalent to accessibility in the model's current context window. v0.4 therefore narrows the recurrence claim to short-horizon contextual recurrence and explicitly leaves long-horizon retrieval for a later experiment.

DuckHunter also demonstrated that separate validators left multiple re-entry paths vulnerable to implementation-like content. v0.4 responds with a single provenance-aware subjective-ingress contract. This is an internal engineering finding rather than an academic source.

## What these sources do not establish

They do not establish that THINK/REST is biologically real, that an LLM has subjective experience, that language is sufficient for cognition, that a continuation probe is a human cognitive mechanism, or that successful behavior demonstrates consciousness.
