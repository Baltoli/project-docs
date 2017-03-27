# Return Values

We want to be able to reason (as far as is possible) about the possible return
values a `CallInst` can give us. The model checking phase can already give us a
1:1 mapping of calls to return values that must be satisfied for a trace to be
be observed.

Worth noting that in the case we are examining initially, all the function call
events are in the same function, reducing the problem to one of intraprocedural
analysis. There may be a way to generalise this to an interprocedural version,
but for now it might be best to stick to intra.

Key insight reached here - `one_acq` and `mult_acq` both fail, but for different
reasons:

* `one_acq` fails **only** because my implementation guarantees that the lock
  won't be acquired first time. If it is acquired first time, then the behaviour
  is correct and it won't fail. How should the checker deal with this
  uncertainty? The hand-coded example did so by using a heuristic.
* For `mult_acq`, some of the traces are impossible to generate - they require
  that the first call to `lock_acquire` returned 0, but that it is then followed
  by a call to the *second* call instance. This can't happen, as the loop
  condition won't be triggered.

An important point to note is that for `one_acq`, there is exactly one trace
through the program - it is the same path whether or not the call returns 0.

Maybe there is some way to think of this as a counterexample generation type of
problem? Or similarly - can we generate a trace that doesn't satisfy any of the
models?

Or maybe the property that I'm trying to prove is too strong?

## Existing Work

So far I haven't been able to find any existing libraries that will do this in
some way - this might be due in part to me not knowing what to actually google
for. Should ask Alan about this when I see him in a couple of weeks.

## Weakest Preconditions

Realised that I think what I've been searching for is *strongest inference* of a
sort. The idea is that for every basic block in a function, we can compute a
logical formula of some kind that expresses the strongest possible inference
about the prior execution of the program. In particular, what we're looking at
here is the values of branch variables on the execution path leading to a basic
block.

For example, the CFG for `do_work` in the example `basic` looks something like:
```
        +-----+
        |entry|
        +---+-+
            |
            |
            |
          +-v+
 +--------+%1+-----+
 |        +^-+     |
 |         |       |
 |         |       |
+v-+       |      +v-+
|%4+-------+      |%5|
+--+              ++-+
                   |
                   |
                   |
                 +-v--+
                 |exit|
                 +----+
```
We loop back into block `%1` if `lock_acquire() == 0`, and progress to `%5` if
`lock_acquire() == 1`.

For each block, there are a set of predecessors. Every predecessor has a branch
condition associated with the branch to the block (e.g. `%1` has branch
condition `lock_acquire() == 0` for `%4`). Therefore the inference for `%4` can
be computed as `inference(%1) /\ lock_acquire == 0`. For `%1`, its predecessors
are `entry` and `%4` (how to handle recursion?). So for `%1`:
```
inference(%1) = (true /\ inference(%4)) \/ (true /\ inference(entry))
...
inference(%1) = true
```
So we see that the strongest inference we can make in block `%1` is `true` (or
equivalently - nothing at all, because we don't know where we've come from).

However, for `%5`:
```
inference(%5) = lock_acquire() == 1 /\ inference(%1)
inference(%5) = lock_acquire() == 1
```
So we see that it's possible to make an actual inference about the previous
execution state when we are in block `%5`!

Bringing this back to traces and models as we have already in the model checker,
the idea is that we generate the strongest inference for every `CallInst` for
which we have an entry in the "must return" mapping. Then, if every strongest
inference is trivial or expressible as a function return value that appears
previously in the mapping, the trace is valid with respect to the model
*including return values*.

## Computing Strongest Inferences

When we check a model with the generative checker, we can extract a mapping from
`CallInst` to expected return value. For every `CallInst` in this mapping, we
will need to compute the strongest inferences for the function containing the
instruction.

So the simplest form of condition we can have is a fixed constraint between a
test value and a constant (`br val b1 b2` gives us `b1:val=true`,
`b2:val=false`). We can also have `true` and `false` as conditions in their own
right.

This algorithm needs to be an iterate-until-convergence algorithm. Therefore we
need to store a mapping from basic blocks to "best known" inference, then update
it as we go.

Then, the algorithm is basically:

* Set the strongest inference for every block to `true` - this is the starting
  point for the algorithm, as it must underapproximate for every block.
* Loop through every basic block:
  * Set the condition for the block to be `\/p. (branch(p->block) /\ cond(p))`
  * How to get the branch condition?

We get a terminator instruction by looping through the predicates of a basic
block. Then, if we have one successor, the branch condition is const true. If we
have two successors, then look at which one goes to the block we're interested
in. If it's the first, then branch is true on the operand, else false.

Don't do anything if we're looking at the entry block - its condition is const
true whatever happens.

## Comparing Conditions

How do we decide if two conditions are actually equal? Obviously this is easy
for ConstTrue and Branch conditions. For Or and And, I think a "stupid"
quadratic algorithm will do the job well enough (on the assumption that there
won't be that many conditions) - for each operand in one component, check if
there exists an operand equal to it in the other.

Maybe it would in fact be best to *normalise* rather than simplify an
expression? Then we would have an easier time doing comparisons.

## Conversion to CNF

So we have a condition made up of propositions (ct, branches) that we want to
convert into CNF. We can then simplify a CNF condition more easily because its
structure is known.

So how do we actually go about doing this conversion? Root propositions (branch,
true) are already in CNF. 

An AND expression is in CNF if:
* There are no nested AND expressions - any that there are can be trivially
  brought up to the top level recursively.
* Every subexpression is in CNF

An OR expression is in CNF if:
* There are no nested OR expressions - again, they can be pulled out recursively
  to the top level.
* There are no AND subexpressions (i.e. it is a pure disjunction of roots)

Then, an OR expression that *does* contain AND subexpressions can be converted
into CNF by distributing over the AND. Of the structure of the OR, we know that
each subexpression is either a root proposition or an AND. Then,
* Convert each AND into CNF.
* Then, generate a cartesian product over the ANDs (i.e. `(a&b) | (c&d)` will
  become `(a|c) & (a|d) & (b|c) & (b|d)`.
* Finally, distribute the non-AND OR terms over this cartesian product to get an
  AND expression in CNF.

So what extra parts do we need to add to the condition interface?

* Methods for flattening AND / OR - no-op on every type except the named one.
* Method for converting to CNF.
* Get rid of simplified interface for now - once we have CNF, simplification is
  much easier.

## Backwards Inference

We want to map branch dependent values onto CallInsts by working backwards. For
my test examples, the simplest version of this analysis will only allow
backwards inference through binary logical operations where one operation is a
constant (at least for now - the approach should be generalisable).

The idea is that we start from a Value and a boolean constraint on its runtime
value. Then, we examine the instruction and its operands to compute a constraint
on another Value. If this is a CallInst, we're done. Otherwise, keep going
backwards until the inference fails.

I think this inference can only be considered within a single basic block, to
avoid issues around the ordering of CallInsts.

## Forward Propagation

I think we would rather propagate constraints forwards to avoid situations like
the block `%6` in `mult_acq` - the info from `%5` and `%9` reaches it at the
same time and they get ORed together. We should start at the entry block and
propagate forwards, maintaining a queue of successors to update (with some kind
of loop threshold to control termination?)

So with a suitable definition of equality and the right simplifications going
in, I think that actually this forward propagation is the way to go (i.e. start
at Or{} for each block, then Or your value onto each successor along with branch
condition, and repeat until convergence).

A key simplification is `A|A(&B) <=> A`, however best this can be implemented.
This method will take us back away from conflating inferences with sequences
(although maybe worth mentioning sequences in the writeup as another possible
approach?)

How do we want to check for termination of the forwards propagation algorithm?
The worked example I went through used a queue of blocks to recheck - maybe go
until the queue is empty, only requeueing successor blocks if the value at a
block has actually changed?

So the algorithm steps are:
* Initialize the entry block to `true`, as we know it is definitely reachable.
  Then every other block is a "maybe" so we set them to `Or{}`.
* Maintain a queue of blocks. Then loop until the queue is empty:
  * Set each successor's inference to:
    ```
    previous_inf | (pred_inf & branch_cond)
    ```
  * Simplify the successor's inference
  * If there has been a change to a successor block, enqueue it

For the types of formulas we're getting out of this new algorithm, we should
rethink how the simplification algorithm will work. What we get out of the
current simplification step is something like:
```
(x | x | [x & y])
```
So the Shannon expansion algorithm is an actual deterministic way to simplify
the inference expressions that we get out of the inference algorithm. In order
to work with them efefctively, we need a bit more machinery for dealing with
manipulations of boolean expressions.
