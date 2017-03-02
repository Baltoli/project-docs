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

## Implementation Design

What actually is a constraint at its most fundamental? It expresses a
relationship between *things* of some kind. For example, that two LLVM `Value`s
are equal, or that all of a set of other constraints are satisfied, or that any
of a set of other constraints are satisfied.

We want to be able to simplify constraints (similarly to the example given
above) into a minimal representation. This isn't really simplification I guess -
it's more of a normalisation process that takes a constraint back to its root
components.

When do we want to emit constraints? Events specify a return value (i.e.
`lock_acquire() == 0`). How should that be integrated into the model checking
algorithm? We can compute (for any given event) the maximal set of constraints
that hold at that event.

Integration into the model checker - when we check an assertion against an
event, it will specify return values etc. We can then associate a constraint
*with that event* if necessary. Then, checking the model succeeds subject to
the constraints on the events being satisfiable. For example, a satisfiable
constaint in `basic` might specify that at the first n - 1 `exit:acquire`
events, the return value was 0 etc. Then will need to design an algorithm that
attempts to solve the system of constraints (or translates them into a format
that an external solver can understand).

So this process outputs the constraints that need to be satisfied for the model
checking to be successful. The dual of this is generating the precondition model
from the event graph! i.e. we know a constraint is satisfied if the constraint
can be shown to be true in the model.

Obviously not all constraints will actually be solvable - if they aren't, we can
emit the minimal / fundamental requirements and show them some other way.

In fact this isn't quite as simple - the initial constraints that we get from
the assertion say things like `lock_acquire() == 0`. We then need to take this
as an assumption and examine the model. We need to validate the constrained
trace against the event graph, which is where things start to get very
symbolic-executiony. Walking the event graph as dictated by the trace, when we
encounter a constraint as below, what do we do to validate it?

What if we were to add specific `Value`s to exit events that correspond to the
return value of the function - so then we can possibly map constraints onto
conditions?

Maybe worth thinking about what we're actually trying to *prove* by using these
constraints. We have:

* Trace representing an execution path through the IR
* Constraints on the return values of functions

And what we want to *know* is:

* Is the trace a valid execution path through the module, assuming the
  constraints that we have?

I guess that "is a valid path through the event graph" is an appropriate proxy
for "is a valid path through the model".

To show that a constrained trace is a valid path through the event graph, we
need to compute the branch condition information and map it back to function
return values with phi-node like info.

Is it possible to map a constraint as shown below onto a specific `CallInst`? If
so, then what we can extract is a sequence of `CallInst <-> return val`
mappings. Then, we could look at the IR to check whether or not such a sequence
is possible. So we are then validating a sequence of return values from a
function against the IR module (however we choose to do that). Question of
partial proof comes up again here I think.

Implementation steps:

* Add `CallInst` to exit events
* Emit constraint sequence when checking every trace.
* Compare constraint sequences to the IR and prove what we can.

Problem when emitting constraints - we don't know which will be the 'right'
constraint to emit when there are several possibilities. The simple / naïve way
doesn't work (as each event is checked several times). We need some kind of
notion of a "satisfying assignment".

```
✓ enter:main
✓ assert:/home/test/tesla-static-analysis/experiments/locks/mock.c:29#0
✓ enter:lock_init:0x8024b3ac0
✓ exit:lock_init:0x8024b3ac0
✓ enter:do_work:0x8024b6840
✓ enter:lock_acquire:0x8024b8b20
✓ exit:lock_acquire:0x8024b8b20 ( == 0 )
✓ enter:lock_acquire:0x8024b8b20
✓ exit:lock_acquire:0x8024b8b20 ( == 1 )
✓ enter:lock_release:0x8024b8310
✓ exit:lock_release:0x8024b8310
✓ exit:do_work:0x8024b6840
✓ enter:lock_free:0x8024b6c30
✓ exit:lock_free:0x8024b6c30
✓ exit:main
```

## Existing Tools

What this is trying to achieve is really a kind of symbolic execution - maybe
worth investigating existing symbolic execution tools to see if they can be
adapted to this use case. Primary contender in this space seems to be Klee.

## Further Improvements to Interface

It's clear that the model checking interface needs more careful thought - the
current abstractions work OK for the very simple property checking, but it's
proving hard to extract more information from them.

Things I've thought about and realised need improvement:

* Sequence checking algorithm being recursive is really a mistake - we can
  probably do better with an iterative version.
* We want to extract even more information when we check an expression
  (motivated by trying to map function events onto the expressions matched).
* Building on the idea of correctness and completeness, we want to know that
  every event in the trace is checked by an expression - this means that the
  shared mutable state approach I have currently is not viable, and we really
  want to be recursively building up some kind of evidence as we go.
* Root idea is that every function & assertion event needs to be *successfully*
  checked by a corresponding expression. What if part of the return value from
  every checker is a map from these events to expressions? So for example, a
  sequence matches a subexpression and receives a map representing the checks
  performed by the subexpression. If the sequence as a whole is successful, it
  can merge together the maps for every subexpression. If it fails, anything
  calling it recursively will not receive incorrect check information!
* This means that every event is then associated directly with the expression
  that it matched against *on the successful path*.
* I think that no events should end up being checked twice, but I need to verify
  this.
* In summary:
  * Root events matching successfully give back a single element map
  * Sequences, boolean merge together the checks performed if successful
  * Merge upwards to get full map of events to expressions
  * Completeness: every 'care' event is matched
  * Other return information: match index, length
