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

In December 2025 I realized that large models would soon operate most of the small models in biological R&D.
LLMs, via AI agents, started to reliably execute work plans of remarkable complexity, in particular in software engineering, but then also in data science, machine learning, and experimental design, that is, the core of computational R&D.

I started working on improving the interface of machine learning and data infrastructure for scRNA-seq data in 2016 with `scanpy`, `anndata`, and other Python data tools.
For 3 years the goal was to reduce the cognitive load & time spent by individual scientists on wrangling files.
During another 3 years of leading computational teams at ML-for-bio company Cellarity in close integration with wetlab & automation teams it turned out that the biggest gains for a team weren't in optimizing an individual scientist's workflow, but in how humans and models would learn and improve together.
I felt it was clear that this would best be achieved through a "shared memory", a query layer that would allow to close larger-scale feedback loops.[^largefeedbackloop]
Now we have these very useful AI agents -- which behave like a mix of junior colleagues, general experts, and small/narrow models -- and the question is whether this changed that premise.

I think it didn't because this new abundance of this peculiar kind of intelligent agency is both completely lost if it's not exposed to the right context and suffers from short context windows & context rot.
Similar to how junior colleagues benefit from supervision with rich & relevant context that lets them find the right way to think about a problem, agents perform remarkable work if they have it or produce unusable slop if they don't.

I don't think that anybody debates this as the key bottleneck of current AI systems, so, I want to spend most of this note on what an optimal shared memory for agents and humans could look like.
I think that's particularly relevant from the angle that observes that a good part of the magic of agents is -- unlike the merely intelligent compute machine that is an LLM -- they can autonomously access context if it's _presented to them_ in the right way.
The layer that achieves this is what I generally want to refer as the "memory layer".

The past year revealed that for now the "right way" seems to be files in storage systems paired with established SQL-based systems of records.
It doesn't seem to be tensors, vector databases, or RAG systems.
I found that interesting because I was never in the "symbolic" camp when it came to developing machine learning models.
So I asked Gemini 3 to clear this up: _Can you disentangle why the symbolic representations in markdown notes & SQL databases, i.e., words and tables representing related concepts, are preferable for persisting thoughts whereas we use tensors for modeling/enabling thoughts in the first place?_

This is what it responded: _We use Tensors to think but Tables to remember.
The distinction you're drawing — between the "Neural Thinking Engine" and the "Symbolic Memory" — is essentially the digital version of the Dual Process Theory in psychology.
Tensors in Neural Nets are for thinking because they are continuous, high-dimensional, and fuzzy. This makes them perfect for inference because it allows: (1) pattern matching & generalization, (2) compression & probabilism, (3) differentiability.
Symbolic Systems like markdown files & SQL databases are for memory because they are discrete, low-dimensional, and rigid. They are preferable for persistence because they display: (1) Perfect Fidelity/ Zero Decay, (2) Addressability & Auditability, (3) Compositionality._[^dualprocess]

I'm trying to arrive at something more concrete, so I ask: _Is it valid to see "reasoning models" as a mix of neural nets trained on symbolic problem solving tasks (like realizing that they made an error, calling a tool, etc.)?_ And it says: _Modern Reasoning Models are Neural networks trained to simulate symbolic execution. Reinforcement Learning on Chain-of-Thought: The model is rewarded for following symbolic rules (e.g., "If I get an error, I must catch the exception and retry"). Internal Symbolic Loops: The "Reasoning" tokens are essentially the model talking to itself in a symbolic language (Natural Language or Code) to "hold" state. It uses the context window as a temporary symbolic scratchpad because its own weights are too fuzzy to hold complex logical state over many steps._[^fuzzy]

I also remembered another angle to argue in favor of "symbolic systems" for holding memory: a 2018 paper from Deepmind on differentiable memory.[^graves18]
Evidently symbolic systems of record aren't differentiable in the sense in which you can write a tensor optimization loop, so it's clear that differentiable (tensorial) memory as presented in that paper fills a gap.
But I'd say that any organization monitoring updates, reviewing changes, e.g. in the context of software development or R&D, runs an optimization process against symbolic systems of records involving human and agentic minds and optimizing their resources.
And with AI agents & robotics, this becomes much more scalable than it was.
Not as scalable as optimizing tensors on a GPU, but maybe scalable enough to merit the question of whether these symbolic systems of record are more optimal than memory stored in tensors?

The "differentiable memory paper" from 2018 did, as far as I know, not make it into real world AI systems and I generally have the feeling that RAG systems and vector databases are much less hyped today than 2 years ago. All the recent approaches to increase context for LLMs revolve around better book keeping of mark down files, better tool calling to existing systems of records, and strategies in which LLMs recursively query storage systems. My understanding is that this is what agents should be doing in almost any setting, but that it has been particularly optimized in the "Recursive Language Models" paper.[^zhang18] And Gemini 3 comments on this: _The reason those systems didn't take over is twofold. Scaling Laws: It turned out to be easier to just make the context window larger (moving toward 1M+ tokens) than to make the external memory differentiable. The Bottleneck is symbolic: The real world is symbolic. In R&D, you deal with discrete entities: molecules, experiments, perturbations, sequences, files, etc. Attempting to force these into a continuous differentiable space for the sake of an optimization loop loses that discrete ground truth._

All of this gives me some comfort because it tells me that AI agents prefer the same kind of symbolic systems that humans prefer.
And so I'm less worried about being out-of-the-loop on what matters most: without tensorial memory I'll always be able to review persistet work results in symbolic systems.
This might both be evident, but because I'm more coming from numerical data that's inaccessible to humans anyway, it seemed plausible that tensorial embeddings would be the main way AI would store results.[^narrowmodels]

It also lets me gain confidence an intuitive idea of what "good memory" should be: just like humans feel the most comfortable and productive with recent symbolic systems of records (hybrids of note-taking & database systems like Notion or Obsidian) agents should feel comfortable & effective in formulating queries to retrieve information about insights of the past.[^gemini3]

[^largefeedbackloop]: It doesn't help to train a narrow model on predicting a drug on 1B cellular omics profiles if the perturbational data underlying these profiles generated in the wetlab wasn't subject to an optimal feedback loop that would govern experimental design. It wouldn't help optimizing experimental design for 1B cellular profiles if the biological systems and perturbations weren't good proxies for clinical problems and so one would first need to close the loop with clinicians and sparse and often low-dimensional or confounded clinical data.

[^dualprocess]: I'm skeptical of the analogy with the Dual Process Theory, but that's for another time.

[^fuzzy]: The weights couldn't hold state even if they weren't fuzzy. Could they?

[^graves18]: Graves, A., Wayne, G., Reynolds, M. et al. Hybrid computing using a neural network with dynamic external memory. Nature 538, 471–476 (2016).

[^zhang18]: Zhang, A. et al. Recursive Language Models. https://arxiv.org/abs/2512.24601.

[^narrowmodels]: And this still holds true for "narrow/small" non-LLM models.

[^gemini3]: I asked Gemini 3 what "efficient memory" should look like, and it says: _For Humans: Efficient memory is "Contextual Retrieval." We need to know why a decision was made. For Agents: Efficient memory is "State and Capability." An agent needs to know the current state of a project and what tools/data are available to change that state._ It was the one response that I didn't find helpful.
