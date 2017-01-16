# AcqRel Data Flow

We are able to detect usages of the `acq_rel` automaton in a manifest,
and set the appropriate field on the Usage message to mark it as deleted
for the instrumenter.

## Data Available

Need to work out what data we have once we've identified an assertion
that uses `acq_rel`, and therefore what the steps will be to do the
optimisation.

* In the *uninstrumented* bitcode, there are calls to the TESLA magic
  functions that get expanded out at runtime. In particular, we're
  interested in `__tesla_inline_assertion`. This represents an assertion
  instance
* There is already logic in `AssertionSiteInstrumenter` that parses a
  call to this magic function into a `Location` message - should not
  have to duplicate.

So the pass starts by identifying the defined automata that reference
the `acq_rel` automaton. Then, it tests each usage to determine whether
that usage is one of the ones that uses `acq_rel`. If it is, then the
pass will then need to perform the data flow analysis on the LLVM
module. 

The data flow analysis is then informed by:

* Automaton bounds. We have an automaton that corresponds to the usage
  in question, and so we can identify the start and end points for the
  data flow analysis to take place. What types of `Expression` can these
  bounds be?
  * Seems to be that sequences can't, but the other temporal assertion
    types can be used (field assignment etc.)
* For now it might well be easiest to restrict the analysis to bounds
  that can be checked at compile time (i.e. function call / return).
  Field assignment would be much harder to do.
* Then, given the bounds we want to:
  * Look up the variable being used in the assertion - how is this done?
    i.e. will want to map the variable to a value in the IR.
  * Then need to start from the starting bound (function call / return)?
    and walk the IR DAG, performing the actual static analysis.

## Analysis

Now given a `Value` representing the lock in question, and the start /
end events, what we need to do is:

* Identify every starting event in the module (this is simplest when the
  start / end are call / return from the same function - then the bound
  is just the function definition). Harder if the starting event is a
  return from.
* Search the IR graph from every start point, looking for calls to
  `lock_acquire` with the given value as the argument. This is where the
  actual static analysis will need to take place - looking at what
  happens to the results of calls and where the control flow ends up
  going. Eventually need to find a single `lock_release` call.
* Worth noting that in some cases, we'll be able to warm the programmer
  about something *possibly* going wrong (i.e. there is some undecidable
  control flow path that might not release a lock). In these cases we'll
  want to keep the instrumentation in place obviously.

This should all be implemented as an LLVM pass that can be run by
`AcqRelPass` on the module that it owns.

## Variable Name to Value

When we call an assertion, it references a variable in the current
scope. How does this get translated into an LLVM `Value *`?

* In the parser we have `ParseArgs` that we've come across before. It
  will end up getting run on each argument to a TESLA macro, drilling
  down into the structure as appropriate.
* The end result of the parsing is a collection of `tesla::Argument`
  objects. These are then put into `Parser::References` at the end of
  parsing (if the argument should be registered).
* The instrumenter then has logic about getting the name of a value in
  scope (`GetArgumentValue`). This populates the argument value based on
  what is in scope.
* This is used at the assertion site to create the instrumentation
  functions (and calls to them).

Now that we know how to get the `Value` corresponding to the arguments
to an assertion, we can perform the analysis.
