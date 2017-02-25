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
