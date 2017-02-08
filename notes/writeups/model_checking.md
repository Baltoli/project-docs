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

### A Tool for Checking ANSI-C Programs (2004)

The main idea of this paper is to build a tool that can check basic safety
properties of C programs (for example, that there isn't any division by zero, or
that unions are not used for type aliasing). It can also check for memory safety
(i.e. that malloc / free are used appropriately).

There's a focus on writing a tool that would be applicable to checking code that
runs as a simulation of a SystemVerilog design, and they have produced a GUI
tool that can be used to explore the state of the system as it's checked.

The implementation is done by normalising the program into a base format to
eliminate a lot of language features (break / continue -> goto, for example).
Then, loops are manually unrolled to a series of if-guarded copies of the body.
An assertion is used at the end to make sure that no more copies of the body are
needed.

Once the transformation is done, the program is converted to a SAT expression
and checked by an external tool.

Counterexamples are generated if possible by the SAT tool, then mapped back onto
the "wound" program.

The tool is available to download and use, and they have tutorials etc.
available for newer versions of the tool. There is no connection with the
runtime behaviour of a program - the tool is a development-time utility.

Note that this is the first application of BMC to C programs, and to software in
general.

### LLBMC: Bounded Model Checking of C and C++ Programs Using a Compiler IR (2012)

Makes immediate reference to bounded model checking techniques from CBMC (note
that the 'bounded' decsription refers to the finite unrolling of loop-like
constructs in the code, so that a finite representation of the program such as a
CNF expression can be generated).

Benefits of using the IR rather than the program text are pretty clear. Same set
of properties (essentially) are checked by LLBMC as CBMC - lots to do with
undefined behaviour, overflow, memory safety etc. The one sort-of temporal
property is malloc / free checking. User assertions are supported, but are no
more expressive than traditional assertions.

After unrolling at the IR level, LLBMC converts to its own logical format
internally. This format 'threads' the memory state through the IR.

The same approach to counterexample generation is taken - find a satisfying
assignment for the negated formula.

This implementation is very similar (morally speaking) to CBMC - the same
properties are verified more or less using similar techniques. The principal
difference is of course that they were able to use the comparatively new LLVM
tools to do it at the IR level, which wasn't a possibility in 2004.

### Model checking C source code for embedded systems (2009)

Focused entirely on the applicability of model checking to embedded systems.
Also references CBMC, but have developed their own checked as well. Design
informed by the differences when running code in an embedded environment (weird
/ proprietary tooling, integrations, runtime environment etc).

Has a list of C/C++ model checkers that would definitely be worth checking out
at some point, and gives an overview of model-checking techniques that aren't
BMC.

Interesting note here - the authors' initial case study using CBMC was to check
temporal properties of a microcontroller program (the "light switch" example).
They found that this was basically inexpressible in a bounded model-checking
context. Note that temporal here is subtly different to TESLA temporal - real
time vs. program logical time.

The checker developed as part of the paper checks the *assembly* code rather
than the C code, using cycle-accurate simulation.

So the conclusion from this paper is that in the specific context of
microcontrollers, C isn't an appropriate abstraction for model checking.

### Morse
* Model checking LTL properties over ANSI-C programs with bounded
  traces, 2015

### Chen
* Model checking one million lines of C code, 2004
