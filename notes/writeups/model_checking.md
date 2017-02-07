# Model Checking

This is a much more general approach to the problem of static analysis
on a TESLA assertion. All my previous efforts have been focused on
analysis in narrow cases (e.g. analysing whether a lock is acquired and
released properly, or whether two functions are called in exact
sequence).

The problem with these analyses is that they are too specific and cannot
be easily composed - the IR analysis carried out for one may be similar
but not totally reusable for another.

However, the design of TESLA as a system for temporal assertions
suggests that there might be a better way. If we were to generate a
temporal logic assertion from a TESLA assertion, then attempt to model
check that against a representation of the IR, we might be able to get
some more useful properties of the software verified.

## Lit Review

This isn't a new idea, and there's a lot of prior work on model checking
for C programs - even one paper that deals with model checking the IR as
we would be doing (probably).

The novel angle comes from the idea that none of the static analysis
we're doing needs to be perfect - if we can't prove something that could
be true, then we can just leave the TESLA instrumentation in place so
that it can take care of it.

This in theory means that any property can be asserted about the code,
it just might not be statically provable.

Analysis and demonstration of this being useful is probably going to
want to come from performance demonstrations and / or bug finding in
code.

### Important Themes & Ideas

* What happens when an analysis is not provable?
* Expressivity of the assertion language - what properties can an
  implementation prove?
* Anything to do with runtime rather than compile time.
* Counterexample generation - is it possible? Can execution paths be
  identified?
* Code released - is anything available to look at or use?

### Clarke
* A Tool for Checking ANSI-C Programs, 2004

### Merz
* LLBMC: Bounded Model Checking of C and C++ Programs Using a Compiler IR, 2012 

### Schlich
* Model checking C source code for embedded systems, 2009

### Morse
* Model checking LTL properties over ANSI-C programs with bounded
  traces, 2015

### Chen
* Model checking one million lines of C code, 2004
