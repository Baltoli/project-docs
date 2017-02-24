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
