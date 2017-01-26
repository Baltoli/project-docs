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

The analysis is constructed from a Module. If also given the bound
function, then the set of functions reachable on the control path ca be
computed. For each of these functions, run the dominance tree analysis
to compute the dominance tree for that function. Then in the same
function, collect all the calls to both the acquire and the release
functions (with the parameter being asserted over). If any release call
dominates any acquire call, then there is an error.

## Call-Dominance

The dominator analysis above shows that at the function level, there is
no calls to release before a call to acquire. The logical next step is
to show this at the module level. The property being shown is that on
the call graph from the bounding function, there is no static way to
reach a function that calls acquire after a function that calls release.

The analysis will be:

* Define a class that represents a simple call graph - maintains a set
  of functions, and for each function has a one-step reachability set.
* Start from a module and bounding function.
* Then put the bound function into one of these data structures, and
  compute its set of one-step reachable functions. For each of the
  reachable functions, put them in a queue and do the same.
* In fact, we don't need to reinvent this data structure. Now that we're
  on LLVM 3.4, we can just compute the actual call graph.

So now given a call graph, what needs to be done is:

* For each function in the module, look at its immediate calls and mark
  them as acquirers / releasers as appropriate.
* Then for each releaser, check that there are no acquirers in its
  transitive call graph.
* This isn't quite right - actually what we want is for there not to be
  any acquirers after any releasers in the transitive call graph of the
  *bound function*. How do we actually want to do this? I think the
  current call graph structure is somewhat inadequate.
* Within a single function, we have no guarantees about the ordering of
  function calls - *unless* we add dominance tree analysis to this?

## FF...T

TODO
