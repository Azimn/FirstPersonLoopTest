# Research Rationale and Source Trail

This file records academic and technical sources that influenced design decisions in Subjective Character Loop. It is an evidence trail, not a claim that the implementation reproduces human neurobiology or establishes machine consciousness.

The project uses biological and psychological findings as **design inspiration and experimental analogy**. When a source is contested or has multiple interpretations, that uncertainty is part of the rationale rather than something to conceal.

## First-person verbal cognition and inner speech

**Design relevance:** Character-accessible cognition is represented as first-person natural language, while implementation state remains outside awareness. This is partly motivated by the extensive literature treating inner speech as a real and functionally varied component of human cognition. The project does not assume that all human thought is verbal.

Alderson-Day, B., & Fernyhough, C. (2015). *Inner Speech: Development, Cognitive Functions, Phenomenology, and Neurobiology*. Psychological Bulletin, 141(5), 931–965. https://doi.org/10.1037/bul0000021

PubMed: https://pubmed.ncbi.nlm.nih.gov/26011789/

## Spontaneous thought, current concerns, and recurrence

**Design relevance:** v0.3 allows thoughts to return from ordinary journal context rather than storing an explicit active-topic object. This is inspired by work showing that spontaneous thought frequently reflects ongoing concerns, goals, future-oriented material, and memory-related content.

Mildner, J. N., & Tamir, D. I. (2024). *Why do we think? The dynamics of spontaneous thought reveal its functions*. PNAS Nexus, 3(6), pgae230. https://doi.org/10.1093/pnasnexus/pgae230

Open article: https://academic.oup.com/pnasnexus/article/3/6/pgae230/7691350

## Unfinished material and continued cognition

**Design relevance:** The continuation probe asks whether a private line of thought still contains unresolved tension. This is not an implementation of the Zeigarnik effect, but evidence that unfinished material is associated with later task-related thought supports testing unresolvedness as a semantic property before adding numerical salience machinery.

Wendsche, J., Weigelt, O., & Syrek, C. J. (2026). *Unfinished work tasks and work-related thoughts during off-job time: meta-analysis of the Zeigarnik effect in a work-recovery context*. Anxiety, Stress, & Coping, 39(4), 385–407. https://doi.org/10.1080/10615806.2026.2616302

PubMed: https://pubmed.ncbi.nlm.nih.gov/41554526/

## Limited introspective access and post-hoc explanation

**Design relevance:** The architecture does not guarantee that a character knows the true hidden cause of its own behavior. It may receive an experienced consequence and interpret it afterward from accessible evidence. This makes future confabulation-style tests possible without building a confabulation module.

Nisbett, R. E., & Wilson, T. D. (1977). *Telling more than we can know: Verbal reports on mental processes*. Psychological Review, 84(3), 231–259. https://doi.org/10.1037/0033-295X.84.3.231

University of Michigan record: https://hdl.handle.net/2027.42/92167

Gazzaniga, M. S., Eliassen, J. C., Nisenson, L., Wessinger, C. M., Fendrich, R., & Baynes, K. (1996). *Collaboration between the hemispheres of a callosotomy patient: Emerging right hemisphere speech and the left hemisphere interpreter*. Brain, 119(4), 1255–1262. https://doi.org/10.1093/brain/119.4.1255

PubMed: https://pubmed.ncbi.nlm.nih.gov/8813288/

Volz, L. J., & Gazzaniga, M. S. (2017). *Interaction in isolation: 50 years of insights from split-brain research*. Brain, 140(7), 2051–2060. https://doi.org/10.1093/brain/awx139

Article: https://academic.oup.com/brain/article/140/7/2051/3892700

## Split-brain caution and contested interpretation

**Design relevance:** Split-brain research is used here as evidence that information access, report, action control, and interpretation can dissociate. It should not be simplified into the claim that split-brain patients contain two cleanly independent persons or that the classic interpreter account settles all questions about unity of consciousness.

de Haan, E. H. F., Corballis, P. M., Hillyard, S. A., Marzi, C. A., Seth, A., Lamme, V. A. F., Volz, L., Fabri, M., Schechter, E., Bayne, T., Corballis, M., & Pinto, Y. (2020). *Split-Brain: What We Know Now and Why This is Important for Understanding Consciousness*. Neuropsychology Review, 30(2), 224–233. https://doi.org/10.1007/s11065-020-09439-3

PubMed: https://pubmed.ncbi.nlm.nih.gov/32399946/

## Natural-language memory in generative-agent systems

**Design relevance:** Generative Agents is useful precedent for maintaining a natural-language record of agent experience and using that record to influence later behavior. Subjective Character Loop deliberately tests a much smaller hypothesis and therefore does **not** import its planning, reflection, or scoring architecture unless later failures justify doing so.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*. Proceedings of UIST 2023. https://doi.org/10.1145/3586183.3606763

Preprint: https://arxiv.org/abs/2304.03442

## Design decisions currently supported by these sources

The evidence above motivates testing, rather than proves, several implementation choices: private language may be extended and internally dialogic; spontaneous thought may revisit ongoing concerns; unfinished material need not be represented by an explicit numeric variable before semantic approaches are tested; first-person reports should not be assumed to contain privileged access to hidden causes; and natural-language experience journals can support persistence and later recurrence.

## What these sources do not establish

They do not establish that an LLM has subjective experience, that verbal thought is sufficient for human-like cognition, that a continuation probe is biologically realistic, that the left-hemisphere interpreter maps directly onto an LLM, or that successful behavior in this prototype demonstrates consciousness. Those stronger claims are outside the scope of this experiment.

## Maintenance rule

When a future architectural decision is materially motivated by published research, add the source here together with a short statement of what decision it informs and what it does **not** prove. Prefer peer-reviewed primary papers, systematic reviews, meta-analyses, or authoritative scholarly reviews. Technical agent projects may be included as engineering precedent but should be labeled as such.
