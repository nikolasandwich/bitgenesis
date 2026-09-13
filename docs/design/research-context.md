# Research context and the next decision

This is a small orientation note based on two primary publications, not a survey
of the current literature. Historical statements below describe those papers;
they do not claim to summarize the latest state of artificial-life research.

Ofria and Wilke's Avida paper describes self-replicating programs with explicit
experimental controls, measurements, lineage analysis and intervention tools.
BitGenesis V0 is more restricted: its engine supplies replication and its genome
only sets a movement probability. We borrow the emphasis on inspectable
experiments; we do not claim to reproduce Avida's organism architecture or scope.
[Ofria & Wilke, 2004, *Avida: A Software Platform for Research in Computational
Evolutionary Biology*](https://cse.msu.edu/~ofria/pubs/2004OfriaEtAl.pdf).

The York workshop report distinguishes observable signs of open-ended evolution
from proposed mechanisms, and discusses multiple kinds of open-endedness. That
distinction motivates keeping measurements separate from explanations rather
than treating complexity, persistence or novelty counts as interchangeable.
[Taylor et al., 2016, *Open-Ended Evolution: Perspectives from the OEE Workshop
in York*](https://www.tim-taylor.com/papers/taylor2016openended.pdf).

## What our own results imply

The following are project interpretations, not results from those papers:

- Campaigns 001–003 provide bounded evidence for inherited variation and
  environment-dependent selection in a designed world.
- Campaign 004 separates population persistence, inherited diversity and ongoing
  generational activity. None alone measures useful innovation.
- The genome has only 1,001 possible values and a single predefined behavioral
  meaning. No amount of extra runtime can expand that encoding into a new sensor,
  memory system or reproductive mechanism under the current rules.
- Changing mortality just to avoid demographic arrest would introduce another
  designed selection pressure. It may be a useful experiment, but is not the
  removal of an assumption or spontaneous emergence.

The next stage should therefore earn its extra representation through a question:
can inherited controllers exploit local sensory information, as demonstrated by
ancestor/randomized comparisons and sensory ablations on held-out worlds?
That remains a V1 design proposal; only V0 runtime is currently implemented.
