# Contributing

Use Python 3.12+ and install locally with `python -m pip install -e .`.
Run `python -m compileall -q src scripts tests` and
`python -m unittest discover -s tests -v` before proposing a change.
Compilation checks syntax in research tools that the contract tests may not import;
it does not execute those tools or verify their results.
GitHub checks the installed package and frozen V0 replay on Windows/Linux with
Python 3.12, 3.13 and 3.14. A replay mismatch needs investigation, not a blind checksum
update; keep the research rules version contract explicit.

Keep changes small and explain the research question, the rules you changed,
and the evidence supporting your conclusion. Add tests for meaningful invariants
and regressions; avoid large frameworks before a concrete experiment needs them.

V0 is the only implemented stage. Discuss later-stage runtime changes with a
design note first. Do not silently change the meaning of existing experiment
configurations: follow [experiment compatibility](docs/design/experiments.md).

Use explicit seeds for stochastic experiments. Record the commit, Python version,
configuration, and raw observations. Distinguish implemented behavior, hypotheses,
and measured results. Keep generated data and secrets out of Git; commit small,
reviewable fixtures only when needed. Do not present a hand-coded strategy as
an evolved behavior.
