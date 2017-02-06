# Call Sequences

One analysis that should be reasonably simple to implement generically
is a sequence of calls to functions.

## Aim

The aim of this analysis is to coalesce a sequence of function calls
like:

```
TSEQUENCE(
  call(f),
  call(g)
)
```

into a shorter sequence if we can prove properties of the dominance.

## Scope

By implementing some methods that compute must call / can call for a
pair of functions, we can possibly do this analysis at an
interprocedural (rather than intra-) level. The analysis is pretty
trivial at function level, but we can make a pretty good go of it at
module level as well.

## Implementation

Within a single function, we can transform `TSEQUENCE(call(f), call(g))`
into `TSEQUENCE(call(g))` if:

* Every call to `g` is dominated by a call to `f`. This means that when
  we reach a call to `g`, we *must* have seen a call to `f`. The case
  where we don't see a call to `g` is handled by the remaining part of
  the sequence.

Within a module (i.e. interprocedurally), we can make the same
transformation if:

* Within the bounds we can compute a call graph, and we can also
  identify all the functions that can / must call `f` and `g`.
* 

Need to choose which method to use - if we have both `f` and `g` being
called in the bound function, or in any function on the call path (*and
nowhere else*) then we can use the simpler intraprocedural version.
Otherwise, the analysis can bail out if it detects any potential
ambiguity. This would take the form of:

* Any function that can call `g` being able to call `f`.

One thing that might be useful is checking for functions that can only
call `f` once - this is really the important property we're looking for.
This is the case in a function if:

* Every terminator in the function is dominated by **exactly one** call
  instance to the function.
* For this dominator, no other call to the function is reachable from
  its basic block.
* We can't call any function that itself calls the function we're
  interested in.

So what we want to check is:

* Find every function that calls `f` exactly once - this obviously rules
  out transitive calls etc, so we know that it's in the right place.
* Then, need to check that every function that *could* call `g` is
  preceded by a call to a function that calls `f` exactly once.
  * How to do this preceding call analysis is a little bit more complicated.
    For a 'could-g' function, we need to look at each call to it. For each call,
    check in its function for a preceding call to a 'must-call-f' function.

But we also have the case where we have something that calls an 'f-exactly-once'
function itself exactly once. So we need something like an iterate until
convergence algorithm that finds all the functions that are transitively
'f-exactly-once'.

So now what I need to do is fix the case where if a function calls the target
*and* makes a call to a function that *can* call it as well.
