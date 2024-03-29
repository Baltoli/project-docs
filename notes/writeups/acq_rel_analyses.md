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

This analysis wants to track where we can get to after spinning on a
lock. Basically, we want to know what can happen if the acquisition
returns `false` compared to when it returns `true`. Because we know from
a previous analysis that there is a branch on the return value of the
acquire function, we can potentially identify BB destinations based on
the result.

We know from prior analysis that there could be intermediate usages of
the return value before we get to the final destination (i.e. the
branch). For obvious reasons, we can't always model this, but for the
simple cases that we've seen before it might be possible. In any case,
supporting a direct branch should definitely be doable. Because the
simplest idiom involves a negated branch, we might end up seeing an XOR
with `true` - possible to symbolically execute something that simple.

So the steps for this analysis will be:

* Identify all the calls to `lock_acquire` in the passed module.
* For each call, look at the usages of the return value:
  * Want to 'trace' each usage of the return value to a branch. It's
    possible that there are multiple usages of the value (e.g. if there
    are different branches based on an unrelated condition).
  * To do this tracing:
    * If a usage is a branch, then we have found the associated branch.
    * If not, then the usage is in some other kind of instruction. If
      it's a 'simple' usage (for now, just binary op. with a constant as
      the other arg), then track the change in symbolic value, and
      search from usages of the new branch.
    * Add the followed usage to the queue to trace, then repeat until a
      branch is found or we can't follow any more.
    * Need to associate it with the root call somehow - if we have
      multiple usages then we want the branch for each root usage. So
      the end result that we get out of this stage of the analysis is a
      mapping from calls to possible branches + expression (e.g. xor T)
      representing how to get the branch choice from the call result.
* Once we have this mapping from acquire call to eventual branch (+
  symbolic expression - lambda?):
  * Identify the destination of the "true" branch (i.e. the one that
    corresponds to the lock acquisition succeeding).
  * From this destination, ensure that we can't call acquire again (i.e.
    the destination doesn't dominate any calls to acquire, and we can't
    call any acquiring functions).
  * If these conditions hold, then we know that after a true return, we
    can't call again.
  * If they don't hold, then this analysis should add a message saying
    why (dominator or function call), then fail.

The mult_acq example was previously detected by the no-branch analysis, but we
need the stronger checks that this analysis can give us. In this example, we
acquire the lock properly both times by spinning, but accidentally do so twice.
So we have something like:

         ---> acq(lock)
        /    /       \
        -false       true
                      |
                  second_acq(lock) // fail because we reach a different call
                                   // after the first call has returned true
            
So we should be able to detect this example using the analysis.

## One Usage

Enforcing the property that a lock is used only once (i.e. it is not
acquired or released multiple times) is covered by the
release-before-acquire analysis and the call order analysis, at least
for now. This is because to use the lock multiple times, it needs to be
released then acquired - a failure case for those analyses.

## Missing Call

This is low-hanging fruit - if there are no calls to either acquire or
release from the bound function, then things are definitely wrong!

## Release Dominators

This is a two-pronged analysis - both inter- and intra-procedural. The
first step is to identify all release calls and store them in a
map indexed by the function in which they appear. Then, for each entry
in this map, compute the dominance tree for the function and check that
there is no dominance relation between any two distinct calls. As well
as this, make sure that we can't call a function that also calls
release.

Instead of dominance, we want reachability.
