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

### Model checking LTL properties over ANSI-C programs with bounded traces (2015)

This is a runtime thing - they build an automaton and weave it into the
executing code (but with an explicit focus on multithreaded systems - they add
an explicit monitor thread rather than having threads monitor themselves
inline).

Evaluation done on the embedded firmware of a medical device, and on a control
application (so a similar focus on embedded systems as the 2009 paper on MCSq
has).

Temporal expressions are on global variables and are essentially pure LTL (e.g.
G(Pressed -> F(Charge > Min)) is the example given). Uses Büchi automata to
express the negated formulae (counterexample finding). Interesting approach is
that these automata allow for acceptance of infinite traces through the model -
maybe worth looking into futher as a checking algorithm.

Their contribution on the practical side is summed up as being a way to express
LTL properties on an *unmodified* program (while TESLA obviously entails
targeted modifications of a program to instrument it).

Model is built directly from the C program rather than from an abstract
representation.

Technique of unrolling loops to a finite depth comes up again.

This is a very interesting paper that I should read in more depth at some point
- lots of interesting techniques and potentially relevant algorithms.

### Model checking one million lines of C code (2004)

Focus on security and safety properties (similarly to TESLA), expressed as
temporal logic assertions of a sort.

Technique for exploring a CFG of a program is pushdown model checking. The tool
built is not sensitive to data flow (i.e. particular values of variables /
memory as the program executes), only to control flow. No support for concurrent
programs.

The paper (as with others) obviously predates LLVM, and so uses syntactic
matching on variables in the source code. Makes a note of the fact that checking
a property statically using model checking is likely to generate false
positives. The things that the authors have checked using MOPS are not
dissimilar to things that could be checked using TESLA, albeit in a
single-threaded environment only.

Tooling support is not dissimilar to how TESLA works in practice - tool to
generate an external description from a C source, and a tool to validate
assertions against this description. There's a discussion of tooling support and
how best to integrate this kind of tool into the compilation process.

The tooling support discussion is interesting - they come up with a solution
whereby the annotations are put into a comment section of the executable files
themselves. This means that the CFG and machine code remain in the same place.
They note that the usability and positive results from their tool are largely
down to how easy it was for them to actually use it on real software with its
own build process - maybe worth looking into with TESLA to a greater extent than
I already have?

## Implementation Design

Need to think about what we want a model checking tool for TESLA to really do
(what the assertions are, how the model is extracted from the module, how it is
checked etc.)

As above, model checking data flow is going to be much harder than model
checking a CFG analysis. A first stab at this is likely to involve only the CFG
for the program. In terms of base TESLA events, this essentially restricts us to
the subset that deals with function calls and returns, assertion sites, and
temporal combinations thereof.

So we'd be able to check things like:

```
eventually(
  ATLEAST(1,
    TSEQUENCE(
      returnfrom(lock_acquire),
      call(lock_release)
    )
  )
)
```

This TESLA assertion specifies how the events are allowed to occur in sequence -
we must have the assertion site before a return from `lock_acquire`, then we
must have `lock_release`, then any number of matched pairs thereafter.

Then, we'd be able to extract the relevant events from the LLVM IR as a
finitely-unwound trace - use some kind of iterative deepening search to attempt
to find a counterexample? How to know when to terminate (from lit review - some
just have a maximum depth that the user can specify) is a problem. Could try to
work out if things are changing or if we're just in a cycle that has no
relevance to the assertion.

Given a counterexample, have the sequence of events that generated it and could
maybe reconstruct the relevant flow control that led to it?

So an initial approach to this will require:

* Extraction of a temporal assertion from a TESLA automaton instance.
  * Will need to recurse into subautomata, and decide which events are
    checkable (and therefore identify maximal checkable assertions?).
  * What will this structure actually do differently to a TESLA assertion? I
    guess it's the recursing into subautomata if we do decide to do that -
    essentially will unwind the whole automaton a bit.
* Extraction of events from an LLVM module into a model of the system.
  * This will essentially be a graph, I think. Nodes in the graph will be an
    LLVM value + some metadata.
* Model checking algorithm that takes an assertion and an event graph, then
  checks it against an assertion.

First pass at this: only function call events.

So a basic block actually defines a *subgraph* that just so happens to be a
linear one. When building a subgraph, we should pass in a reference to a set so
that we know which events have been seen. Then this means that a basic block
returns us a graph that doesn't know about its successors?

Unrolling functions - when we encounter a function call, emit a call event,
unroll the function emitting all events, then emit a return event.

So what we want to do really is build a graph for each function in the module
(memoized - so that we either compute if needed, or look it up in the table). So
when we first encounter a call event, we check if that function has an entry in
the table. If not, we compute its event graph and store it, and if so, we just
look up the stored graph.

We want graphs to have a single entry and exit point so that they can be spliced
together.

How do we handle recursion??? Set of incomplete functions so that they can just
point back?

So now we have a more flexible way of handling graphs of events. Next logical
step is a generic graph transformer I think.

## Extracting Assertion Sites

In order to check basic TESLA assertions I need to be able to extract
assertion site events. These are (I think) represented as magic function
calls - so need to possibly change call graphs before expanding into the
module graph to capture these as assertion sites.

In a module, we should extract assertion sites *before* doing any
expansion of the call graph. Before instrumentation is done, we should
extract the special call instances as assertion events. These will be
calls to `tesla_inline_assertion`, and we can map back onto an automaton
location by extracting the global string argument from the call.

This will then give us an event graph that includes inline assertion
events as well as function entry and exit. In particular, we can get a
location precisely from arguments 2, 3 & 4 of these calls. Then to get
the automaton, we'd have to take in the manifest file and look it up.

## Checking Assertions

So we want to check a particular TESLA assertion against an end graph.
Need to define what it means to actually check something first - we
would like to:

* Take in a manifest and an event graph.
* For each usage in the manifest, decide whether it can be statically
  proven true or not.
* If it can, delete the usage.

What is our current notion of provability?

* Assertions are sort-of LTL, which means that our notion of truth is an
  all-paths type of notion. That is, we need to prove the assertion on
  every path through the graph.
* Unit to be checked against is a TESLA `Expression` (as defined by the
  protobuf specification). These are the core units of logical
  statement.
* Use the formula-reduction sort of algorithm to check at a state:
  * null events true in any state
  * function call events true in a state that calls the function
  * assertion site events true in a matching state
  * subautomaton recurses
  * sequence is true if the first part matches and the second part
    matches at all successors, XOR if the whole sequence matches at the
    successor (as it doesn't make sense to have both).
  * boolean expression just computes the truth value for each expression
    in sequence, then reduces them appropriately.
  * others like repetition, optional can also be encoded

So the core algorithm will take an `Event` and an `Expression` and
attempt to check them against each other. Extend to a graph by checking
from the entry nodes to the graph.

Some expression types are not provable for now - field assignment etc.
These are false in every state, so any TESLA assertion that uses them
will be left alone.

Things like value specification and arguments will need data flow
analysis, but in the future we'll be able to add constraints of two
kinds to them:

* Argument restriction specifies that the value used as an argument must
  have a particular value for the assertion to hold.
* Return value specifies the same but for return values.

From these we can build up a set of constraints that must hold in order
for the assertion to be satisifed - all path constraints so this will
hust be a big set union I think (i.e. if path A requires constraint α
and path B requires constraint β for the assertion to hold, then for it
to hold in general we need both to be true). Future work could then
analyse these constraints to see when they can be true.

Should also point out the state that fails an assertion (i.e. give the
expression it should have satisfied and why it doesn't).

## Bounded Model Checking

We have loops so a traditional model checking algorithm seems to be
basically not viable - what it's trying to verify gets *very* confusing,
and traces were complex.

New approach inspired by lit review is to generate paths of a given
length through the graph. Then a property can be checked on paths up to
a given length as an approximation of provability.

Need to come up with a way of generating these paths. Basic idea is that
a path is just a vector of events - because we know it's linear, we can
just shove the events into a vector without worrying about graph
ownership or successors.

The paths of length 1 through the graph are just the entries, the
recurse from there. Most natural thing is to have the function give
paths of length *up to* n.

Start from n-1, then for each path look at the last element and add a
new path that's the same but with a successor on the end.

Algorithm for checking a TESLA assertion against a *terminating* trace.
Will operate similarly to the failed attempt at doing this on a general
tree (i.e. for a given trace, check an expression recursively). Should
maybe try to formalise the TESLA <-> logic mapping?

The new checker interface needs to take a const reference to a trace,
and an index into the trace.

Problem: the new sequential checker is too permissive. It will accept
invalid sequences because it just *ignores* events rather than failing
an assertion.

At any point while checking a sequence, we know what the current head of
the sequence is. So instead of trying to match the head, we walk through
the trace trying *every* assertion in the sequence:

* If the head matches and none other do, match the tail from the next
  spot.
* If the head doesn't match and no others do, move on a spot.
* If any others match, fail!

Note that "others" has to mean any that are not equal to the head (suing
the protobuf equality).

Need to come up with a proper definition of the sequence matching
algorithm - if I can do that then the checker will work I think.
