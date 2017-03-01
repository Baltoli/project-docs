# Event Constraints

TESLA assertions are more expressive than simple function / call return with
assertion sites (as the model checker currently implements). In particular, it
allows for the particular value of a function return to be specified.

We need to work out a way of augmenting the event graph with information
relating the value of function returns.

## Basics

The event graph is constructed as follows:

```
Basic Blocks
    |
    v
Instructions
    |
    v
Relevant Instructions
    |
    v
Assertion Mapping
    |
    v
Call Expansion
```

Every function call will have an associated LLVM value. The first step of this
analysis is probably to augment function exit events with the corresponding
value, so that we have the information in the graph.

## Data Flow Analysis

The `acq_rel` based examples that need constraint analysis to solve are all
simple (in that the return value is a boolean that directly informs a branch).
In general, however, this won't necessarily be quite as nice.

I think that a solution for the boolean cases that I have is possible, but might
not be easily generalisable to harder constraints on values (e.g. an arbitrary
integer value).

What we would really like to be able to do is perform a general data flow
analysis on function return values that gives information at an event about
previous return values.

As far as I can see, the only way we have to constrain the return values so far
in a program is the *branch* we are currently on within a function.

We can compute a set of constraints on reachability for individual instructions
in a function as follows:
* The entry to the function has `true` as its only precondition.
* The preconditions for the target of a branch are the logical AND of the
  appropriate branch condition and the basic block entry precondition.
* Basic block preconditions are the logical OR of all their predecessors'
  postconditions.

Need to be a little bit more rigorous with the language here. More formally:

* Every basic block has a precondition associated with it. The precondition
  *must* hold when entering the basic block (examples: entry block has `true` as
  a precondition, dead blocks have `false`).
* Basic block terminators generate an indexed family of *postconditions* that
  hold when the block exits (each member of the indexed family corresponds to a
  different successor block).
* Postconditions are computed as the logical `AND` of the block's precondition
  and the appropriate value constraint (e.g. that a particular LLVM value
  evaluated to `true`).
* Preconditions are the logical `OR` of all possible postconditions of
  predecessor blocks.

Now need to turn this into an actual algorithm that can generate constraints for
a particular function.

How to handle loops? From working a simple example out by hand on paper, I think
an iterate-until-convergence algorithm will handle them appropriately (though
simplification of equivalent constraints is needed).

### Constraint Generation Algorithm

* Start from the entry basic block, and set its precondition to `true`.
* Examine the terminator for the block to see which block is the target when the
  condition is `true`, and which is when `false`. Then set the preconditions of
  those blocks to be (branch value `AND` current precondition) `OR` the
  successor's precondition if it has one.
* Repeat until convergence.

It might in fact be useful to use some kind of phi-node like abstraction instead
of logical `OR` in preconditions - gives us more information about previous
states we were in.

Then need to map all of this back onto the event graph we extract from the
module:

* Initial computation of constraints is on the basic block level, and
  instructions within a basic block will inherit the preconditions associated
  with the block that they belong to.
* Then, call instructions get mapped onto entry and exit events. Entry events
  correspond directly to the call, and so they can have the same preconditions
  as the call event. Once we pass an entry event, the "context" changes and
  we're inside a different function.

It might initially make sense to compute constraints on functions. The entry and
exit events are generated initially with the function that they correspond to.
How will conditions be changed when we splice function instruction graphs
together? When we splice a function graph in instead of a call instruction, the
graph as a whole will need to inherit the conditions at the site it is spliced
into (i.e. if we have a call instruction with precondition `P`, then the
function graph will have precondition `P` at entry and *all* of the conditions
will need to be recomputed)

Where do constraints come from? They are an arbitrary LLVM value but we would
like to be able to map them back onto constraints on a function call(s). For
example, the branch in `do_work` in the simple lock examples is on a value
computed by `xor` with the function call value.

We should be able to generate a set of constraints from binary operations -
eventually we go back to things we can't resolve (function return values,
parameters) or to things we can (constants, globals).

For example, `%3 = xor %2, true` would generate a set of constraints like:

```
%2 = true AND true = false
%2 = false AND true = true
```

Which after suitable simplification will become `%2 = false`.

Then we know that `%2 = call lock_acquire(...)` so `%3 = true` eventually
implies that `lock_acquire(...)` must have returned `false`.

A similar analysis might end up placing constraints on parameter values to the
function, for example.

## Existing Tools
