# Active Inference as a Placement Strategy in the ECLYPSE Edge-Cloud Continuum Simulator

## Abstract

## Glossary

Good call to include one given the cross-disciplinary readership (CS
infrastructure people won't know AIF terminology; AIF people won't
know ECLYPSE/edge-cloud terms). Keep it short — 10–15 entries max.

## Introduction and objectives

### Inspiration: 
1. https://deniseholt.us/the-dawn-of-true-ai-agency-why-active-inference-is-surpassing-llms-and-shaping-the-future/
2. OVF, my new workplace, plans to employ AI for resource management

The two listed inspirations are uneven in weight. The blog post
(Denise Holt on LLMs vs AIF) is a popular-science piece — it's fine as
a motivational anecdote, but if it's a reference it'll look weak in an
academic submission. Consider citing a primary source instead (e.g.
Friston et al. on active inference, or a position paper on AI for
resource management). The OVF motivation is legitimate and worth
keeping, but frame it as a practical context rather than an
inspiration — reviewers may read "my new workplace" as a conflict of
interest signal if it's phrased casually.

Objectives should be stated explicitly here: (1) verify ECLYPSE
reproduces the paper's results, (2) implement AIF as a placement
strategy, (3) evaluate against BestFit under realistic failure dynamics.



## Related work

the original ECLYPSE paper, PyMDP / the Friston discrete-POMDP
formulation, at least one or two edge-cloud placement papers (BestFit
variants, service placement surveys), and ideally one paper applying
AIF to resource management or networking (there are a few from
2022–2024)

## Materials and methods

### Codes

### Data

---
a subsection on the experimental setup (infrastructure parameters,
kill/revive rates, application topology, simulation duration) — that's
the content that lets someone reproduce your results and is distinct
from "here is the code" and "here is the data".

## Partial and negative results

### Algorithms implemented in the load balancer of Kubernetes

### Warming up: re-creating the plots of the ECLYPSE paper
the discussion subsection should explain why your plots differ from
the paper's (different seeds? different ECLYPSE version? stochastic
noise?). Make sure you have a clear answer before writing it.


UC1:
3x1 plot
3x3 plot

UC2

UC3

#### Discussion
Why they are different from the paper's plots



### AIF as a placement strategy without revival
this is the 90%+ unreachable case. The discussion here should land on
the lesson: dead-node exclusion requires explicit availability
requirements on services, and equilibrium kill/revive rates matter
enormously.

#### Discussion

## Results
AIF with realisitic revival rate and 12 months simulation time

This needs to expand into at least: (a) the main comparison figure
(12-month BestFit vs AIF), (b) the headline numbers (latency,
unreachability rate, 100%-spike count, effective delay), and (c) the
AIF ***action distribution*** (how often did it choose pack/spread/balance
and does it correlate with calendar phase?). That last one — action
distribution vs phase — you haven't plotted yet and it could be a nice
additional figure. ***phase plot***

## Discussions

### Further directions
- learned B-matrix (rather than hand-coded transitions),
- multi-application AIF, 
- AIF with bandwidth/latency as observation modalities, 
- real hardware deployment.


## References
- ECLYPSE
- the works you have mentioned when explaining the four pillars
those were Friston et al. (2017) for EFE/Active Inference, and PyMDP.
I'd compile the full citation list before writing to avoid gaps.


## Appendix A: Software
The code will be in github.

### Downloading and unpacking

### Building

### Running

### Plots

