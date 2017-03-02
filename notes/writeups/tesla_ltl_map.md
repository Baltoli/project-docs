# TESLA as LTL

## Introduction

This writeup describes how the semantics of a TESLA assertion can be
compared to a linear trace of an event graph.

The types of events that we currently extract are:

* Function entry & exit, tagged with the corresponding LLVM function
* TESLA assertion sites, tagged with a source location

## TESLA Expressions

A TESLA assertion is a composition of expressions (sequences, booleans,
function events etc.). We would like to have a semantics for these
assertions in terms of how they are applied to a linear trace.

* **Booleans**: checked by checking each subexpression at the current
  state, then reducing the results together with the appropriate
  operation.
* **Null**: true in any state.
* **Sequence**: true in a state if the sequence occurs somewhere in the
  future from the current state - either the head of the sequence
  matches, and we match the tail at the successor, or we match the whole
  sequence at the successor.
* **Assertion**: direct comparison at the current state.
* **Function**: direct comparison at the current state.
* **Field Assignment**: not currently checkable - always false.
* **Identifier**: gets the named automaton and checks it at the current
  state.

It's worth noting that this formulation relies on single TESLA
assertions being encoded as a sequence with one element - this means the
recursing logic can live entirely in the sequence checker. If I find
that this isn't in fact the case, then each checker will need to run
along the vector and return the state in which it was first satisfied
(so that the next checker can go from there).

## Sequence Checking

This part of the algorithm is the most complex by far. A TESLA assertion
that is a sequence specifies a list of events `A B C D ... ` that must
occur *exactly* as specified by the list.

A sequence assertion fails if:

* An event occurs when it is not expected to (for example, if `C`
  occurred when we were expecting `B` in the example above).
* We reach the end of the trace and there are still events left to
  observe in the sequence.

The failing approach from yesterday took the approach that if we first
matched an `A` event, we could then proceed to check the tail sequence
`B C D` on the remaining trace. This is not a correct interpretation of
the semantics of a sequence - if we saw another `A` event, there would
be a runtime failure!

Essentially, a sequence specifies a set of events that we care about,
and the order in which it is permissible to observe them in. Any other
events not named in the sequence are "don't care" events that can be
ignored.

At any given point in the checking of a sequence, we have:

* A model state being checked against
* The sequence and an index into the sequence giving the expected
  current event.
  * From this, we can get the set of events we care about.
  * If the expected one matches, then we're all good
  * If it doesn't, and one of the others matches, then fail
  * If none match at all, then move on and try the next event

Subautomaton checking presents a subtlety - because they themselves
might name a sequence of events, we might not actually want to be
checking them as one of the "other" events. I think for now just
ignoring them and only checking other kinds of expression makes sense.

There are still subtleties with how this will work - things like boolean
expressions aren't so clear cut, so it would be good to have a more
formal notion of how they interact with this mechanism.

## API Changes

Perhaps a better API design would be to have checkers return the index
of the end of their match? Should investigate how this would work in the
future.

This makes more conceptual sense for the API design I think. The 'simple'
matches like function entry / exit and assertions will match only a single
state and return the next state, while subautomata and sequences will match a
longer range.

Boolean expressions present an interesting question - what should their matching
range be? Sensible options are:

* Match zero length (analogous to PEG combinators)
* Match the longest length of a subexpression

Additionally, individual checkers need to be able to return a failed result.
This means that the type we're looking for is really `Maybe Length`. Have
implemented this type as a simple wrapper around a length.

Now want each individual checker function to use this type instead of bool,
wrapping their results as appropriate.

### Sequence Checking With New API

We should now be able to check sequences properly with this new API. Problem
before was that we were 'forgetting' the events that we didn't want to see, and
that multiple events could be recognised at one time.

How to resolve these properly?

* The sequence checker function needs to take an extra parameter representing
  the set of expressions we care about seeing. If this set is populated
  initially, then we don't need to populate it again (as we're in a recursive
  sequence check). If it's empty, then put every expression in the sequence into
  it.
* Then when checking, we make sure that we don't observe any extra events.

The checking algorithm will iterate through the trace starting from the give
index. When it finds a match for the head, get the length and recursively check
the tail against it with the set of expressions we care about not seeing.

We might need a slightly subtler notion of what these expressions are at some
point in the future.

Problem: the current approach to picking expressions that we want to ignore is
too sensitive. Lots of things will match in lots of places (for example, the
`lock_release` subautomaton matches `entry:main`, causing a failure - this isn't
intuitively what we want at all!)

The solution (I think) is to extract *basic* subexpressions from an expression
recursively. That way we can exactly specify what subexpressions should be
banned and which should not be checked for failure. Consequently, we will only
experience a failure at a state if it is precisely one of the banned events.

Problem I'm experiencing currently is caused by (as an example) us adding all
the subexpressions for `acq_rel` into the set at the beginning. Then, when we
finish checking `acquire`, we look to make sure that there are no future events
BUT we have the ones from `release` so they get flagged as failures even though
they will be picked up by a future check.

The root cause (to an extent) is therefore the direct recursion into
subautomata. Each individual subautomaton has a set of events it cares about,
but this can overlap with others. The implication of this seems to be that model
checking isn't necessarily as simple as model checking a formula...

Idea: restrict lookahead to cases only where a subautomaton is the *last*
subautomaton mentioned in a sequence **and** whose parent subautomaton meets the
same condition.

Need to work out how to map this into the checker. The idea is that 'future'
failures for subautomata will be handled by the next ones along in the sequence
if necessary, and by lookahead *only* at the end.

## Repetitions

Currently, the sequence checker is *not* adequate as it completely disregards
the number of repetitions that a sequence is permitted to have. This means that
things like looping on lock acquisition are just totally broken on longer
traces.

A sequence expression can be repeated between `minReps` and `maxReps` times. The
sequence checker we have will check exactly one iteration of the sequence. What
we probably want to do is have a new checking function (`sequenceRepeat`?) that
also takes a sequence, but will respect the number of repetitions allowed. It
will call the existing function repeatedly until failure OR it hits the maximum
number of repetitions. If the number of successful repetitions is less than
minreps, return a failure.

Problem: we can't distinguish between a regular failure and one caused by
lookahead. This means that there is effectively no difference between failing
because the sequence stopped happening and because there were lookahead
failures.

Alternative: when checking a sequence once, ignore lookahead failures. Move the
logic for handling them up a level into the repeated sequence checker. When we
have matched as many sequence iterations as possible, then look at the events
left.

If we do this, we still need to work out *when* to actually do lookahead, as
it's not always the right thing to do. Idea keeps coming back that we need to
look at the ends of sequences somehow - I think I'm close to figuring out what
the solution is. Key will be properly characterising when to perform the
lookahead checking on future events (or a completely different formulation of
the checking algorithm that makes things conceptually neater!).

## Correctness and Completeness

Currently, the checker will determine whether or not the trace is *correct* with
regard to the TESLA model. Correctness captures the idea that the trace can be
described by the model (that is, some subset of the trace is validated by the
model). Completeness will aim to capture the idea that every event in the trace
is accounted for by an assertion - if we have an event that can occur without
being accounted for, then there would be a runtime failure.

To check completeness, what we need to implement is:
* Tag each event in a trace with `false`
* Compute the set of all subexpressions for the root expression being checked.
* For each event in the trace, if it matches *any* of the subexpressions, then
  keep it as `false`. Otherwise, it's a "don't care" expression that can be
  marked as `true`.
* Then in the correctness check, when we successfully match a basic
  subexpression, tag the corresponding event as `true`.
* If any events remain `false` after checking, then they are not accounted for
  and the analysis is unsafe.

Tagging mechanism seems to work, but need to roll back in the event of failure.
Turns out that we didn't actually need to roll back - the solution was actually
to just use a copy on the initial tagging phase (as it relied on `CheckState`
itself).

## Checking Cycles

The algorithm will be different when checking cyclic traces (as opposed to the
bounded traces so far), but I think the core logic will remain the same. A
simple approach (not sure of correctness yet) would be to allow for the
correctness part of the check to fail, but enforce completeness. The idea here
is that the assertion might not be completely satisfied if we end up in a cycle,
but if every event seen in the cycle has been validated by an assertion, things
are OK.

## Boolean Expressions

Need to more concretely check how boolean statements interact with the checking
algorithm. The core question is whether or not a boolean expression in an
assertion should be able to mark an event as checked - that is, if we're
checking a boolean expression, should we make a copy of the tags so that the
changes don't get reflected globally? In the examples so far, it doesn't seem to
matter, but there might be cases where it does (or is dependent on the operation
in the boolean expression).

Easy answer for now is that we want to check off events inside boolean
expressions - demo is to copy `tr` in the boolean matcher, and the analysis is
incorrect when running on `basic`.
