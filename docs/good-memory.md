---
title: "Good memory for biological R&D"
date: 2026-02-27
author: falexwolf
orcid:
  falexwolf: 0000-0002-8760-7838
affiliation:
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lamindata
repo: https://github.com/laminlabs/lamindb
tweet: TBD
linkedin: TBD
---

What should a good shared memory layer for agents and humans look like?

---

In December 2025 I realized that large models would soon operate most of the small models in biological R&D.
LLMs, via AI agents, started reliably executing work plans of remarkable complexity, in particular in software engineering, but also in data science, machine learning, and experimental design.

I started working on improving the interface of machine learning and data infra for scRNA-seq in 2016 with `scanpy` & `anndata`.
The goal was to reduce the cognitive load & time scientists spend on wrangling data.
After transitioning to leading computational teams at the ML-for-bio company Cellarity in close integration with wetlab & automation teams, it was evident that the biggest gain wasn't in optimizing for the individual scientist, but for how humans and models would learn and improve together.
I felt it was clear that this would best be achieved through a "shared memory layer", a query layer that would allow teams to close larger-scale feedback loops.[^largefeedbackloop]
Now we have these very useful AI agents -- which behave like a mix of junior colleagues, general experts, and small models -- and I wonder whether this changed that premise.

For a moment, I was worried that the premise changed and I might have worked on the wrong problem all these years.
In the next moment it was clear that it didn't because this new abundance of this peculiar kind of intelligent agency is completely lost if it's not exposed to the right context.
On top of that, it suffers from short context windows & context rot.
Similar to how junior colleagues benefit from supervision with rich & relevant context that lets them find the right way to think about a problem, agents perform remarkable work if they have context. And they produce unusable slop if they don't.

I don't think anyone debates that this is the key bottleneck of current AI systems, so I want to spend most of this note on what an optimal "shared memory layer" for agents and humans could look like.
I think that's particularly relevant from the angle that a good part of the magic of agents is -- unlike the merely intelligent compute machine that is an LLM -- their ability to autonomously retrieve context if it's _presented to them_ in the right way.
If you will, agents can solve their own biggest bottleneck if "context engineering" is done right.
In this note I want to refer to the "layer" that achieves this as the "shared memory layer".
This is complementary to studying the procedural context engineering problem.

The past year revealed that for now the "right way to present context to agents" seems to be files in storage systems paired with established API-based systems of records.
It doesn't seem to be tensors, vector databases, or RAG systems.
I found that interesting because I was never in the "symbolic camp" when it came to developing machine learning models.
So I asked Gemini 3 to clear this up: _Can you disentangle why the symbolic representations in markdown notes & standard SQL databases, i.e., words and tables representing related concepts, are preferable for persisting thoughts whereas we use tensors for modeling/enabling thoughts in the first place?_

This is what it responded: _We use Tensors to think but Tables to remember.
The distinction between the "Neural Thinking Engine" and the "Symbolic Memory" is essentially the digital version of the Dual Process Theory in psychology.
Tensors in Neural Nets are for thinking because they are continuous, high-dimensional, and fuzzy. This makes them perfect for inference because it allows: (1) pattern matching & generalization, (2) compression & probabilism, (3) differentiability.
Symbolic Systems like markdown files & SQL databases are for memory because they are discrete, low-dimensional, and rigid. They are preferable for persistence because they display: (1) Perfect Fidelity/ Zero Decay, (2) Addressability & Auditability, (3) Compositionality._[^dualprocess]

I'm trying to arrive at something more concrete, so I ask: _Is it valid to see "reasoning models" as a mix of neural nets trained on symbolic problem-solving tasks (like realizing that they made an error, calling a tool, etc.)?_ And it says: _Modern Reasoning Models are Neural networks trained to simulate symbolic execution via two concepts. (1) Reinforcement Learning on Chain-of-Thought: The model is rewarded for following symbolic rules (e.g., "If I get an error, I must catch the exception and retry"). (2) Internal Symbolic Loops: The "Reasoning" tokens are essentially the model talking to itself in a symbolic language (natural language or code) to "hold" state. It uses the context window as a temporary symbolic scratchpad because its own weights are too fuzzy to hold complex logical state over many steps._[^fuzzy]

I also remembered another angle to argue in favor of "symbolic systems" for holding memory: a 2016 paper from DeepMind on differentiable memory.[^graves18]
Symbolic systems of record aren't differentiable in the sense that you can write a tensor optimization loop, so it's clear that differentiable tensorial memory as presented in that paper fills a gap.
However, I'd say that a team that monitors updates and reviews changes, e.g. in the context of software development or R&D, runs an optimization process against symbolic systems of records.[^ultimate]
And with AI agents & robotics, this becomes much more scalable than it was.
Not as scalable as optimizing tensors on a GPU, but maybe scalable enough to merit the question of whether these symbolic systems of record are more optimal than memory stored in tensors, at least for present day real-world systems?

The "differentiable memory paper" from 2016 did, as far as I know, not make it into real world AI systems and I generally have the feeling that RAG systems and vector databases are much less hyped today than 2 years ago.
Most recent approaches to increase context for LLMs revolve around better bookkeeping of markdown files, better tool calling to existing systems of records, and strategies in which LLMs recursively query storage systems.
My understanding is that this is what agents should be doing in almost any setting and that it has been particularly optimized in the "Recursive Language Models" paper.[^zhang18]
Gemini 3 comments on this: _The reason those [differentiable memory] systems didn't take over is twofold. (1) Scaling Laws: It turned out to be easier to just make the context window larger than to make the external memory differentiable. (2) The bottleneck is symbolic: The real world is symbolic. In R&D, for example, you deal with discrete entities: molecules, experiments, perturbations, sequences, files, etc. Attempting to force these into a continuous differentiable space for the sake of an optimization loop loses that discrete ground truth._

All of this gives me some comfort because it tells me that AI agents prefer the same kind of symbolic systems that humans prefer.
And so I'm less worried about being out-of-the-loop on what matters most: I'll always be able to review persisted work results in symbolic systems.
This might be evident for language models, but because I'm coming from numerical data that's inaccessible to humans anyway, it seemed plausible that tensorial embeddings would be the main way in which AI would store results already in the near future.[^narrowmodels]

All of this lets me also gain confidence in the simple intuitive idea of what "good memory" should be: similar to how it seems that humans feel more comfortable & productive with the advent of recent symbolic systems of records (hybrids of note-taking & database systems like Notion or Obsidian), there should be similar systems that make agents "feel" comfortable & productive in formulating queries to retrieve the context they need.[^gemini3]

[^largefeedbackloop]: It doesn't help to train a narrow model on predicting a drug on 1B cellular omics profiles if the perturbational data underlying these profiles generated in the wetlab wasn't subject to an optimal feedback loop that would govern experimental design. It wouldn't help optimizing experimental design for 1B cellular profiles if the biological systems and perturbations weren't good proxies for clinical problems and so one would first need to close the loop with clinicians (and often sparse, low-dimensional, or confounded clinical data).

[^dualprocess]: I'm skeptical of the analogy with the Dual Process Theory, but that's for another time.

[^fuzzy]: The weights couldn't hold state even if they weren't fuzzy. Could they?

[^graves18]: Graves, A., Wayne, G., Reynolds, M. et al. Hybrid computing using a neural network with dynamic external memory. Nature 538, 471–476 (2016).

[^ultimate]: The optimization objective of a new medicine or material targets the creation of a discrete symbolic entity whose formula will be stored in a system of record.

[^zhang18]: Zhang, A. et al. Recursive Language Models. https://arxiv.org/abs/2512.24601.

[^narrowmodels]: And this still holds true for "narrow/small" non-LLM models.

[^gemini3]: I asked Gemini 3 what "efficient memory" should look like, and it says: _For Humans: Efficient memory is "Contextual Retrieval." We need to know why a decision was made. For Agents: Efficient memory is "State and Capability." An agent needs to know the current state of a project and what tools/data are available to change that state._ It was the one response that I didn't find helpful.
