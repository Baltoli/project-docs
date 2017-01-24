# AcqRel Analyses

This documents the individual static analyses used on the
`acq_rel` automaton.

## Other Lock

A simple analysis that checks whether or not there are any *statically
reachable* calls to the acquire or release functions that take a
different lock as their argument (to the one beign asserted about).

This analysis just checks every call site to those functions, then
checks their parameter against the one identified by the argument
collection procedure.

## Branching

The specification of the lock automaton states that there must be a
sequence `FFF...T` of calls to the acquisition function. If there are no
branches on the results of the acquisition function, then it's very
likely that the behaviour is incorrect.

This analysis therefore checks whether there are any calls to
`lock_acquire` that do not have a branch dependent on the result.

Interesting part of this analysis is that usages are unlikely to be
immediate - we should be able to track them through simple operations
(i.e. LLVM binary ops). Any more complex usages (function calls, control
flow etc.) should not be considered for now. The way to do this is
probably to use a queue to track places we are following usages to.

## Dominators

If any call to `lock_release` dominates any call to `lock_acquire`, then
there is a static path on which we have release-before-acquire.

The LLVM pass that gives a dominance tree is a function pass, so this
analysis can only be done at a per-function level (i.e. warning of r-b-a
can only be done if the calls are within the same function). This is
still a useful thing to be able to verify.
