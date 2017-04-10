# Lit Review

Summary of my lit review and background reading for my dissertation.

## Bounded Model Checking

* CBMC paper references 1999 paper (symbolic model checking without
  bdds)
* aim of this paper is to perform symbolic model checking (where the
  state space of the system isn't explicitly constructed - note that my
  system does *not* do symbolic model checking. why not?)
* symbolic model checking (remember from pII course) uses *state
  variables* - we build explicit event graph.
* they mention not having to construct automata as an advantage, and
  link bounds to counterexample generation
* they build a mathematical semantics of bounded model checking in the
  context of LTL, looking at cases with & without loops
* the key theorem that they use is that you can prove an existential
  path formula (E[f]) by proving it for some finite bound k
* from there they prove results about diameter of structures to limit
  bounds
* they also provide an implementation of their techniques and apply it
  to some model checking problems (verifying the behaviour of adders
  etc.)
* their checker deals with Kripke structures - you have to 'compile'
  your program into this to use it
* this is the first appearance of *bounded* model checking, however.
  sets up the theory in the context of symbolic model checking

* next reference followed from CBMC - 2003 paper by some of the same
  authors on verifying C programs against Verilog implementations
* Edmund Clarke is the name that runs through all of this research -
  he founded model checking in its entirety with Emerson in the 80s
* seems to be an initial focus of bounded model checking as a technique,
  still very focused on boolean and symbolic model checking
* the key idea here is really that the C program can be used as an
  *executable specification* for a hardware design, but the kicker is
  that you can do anything you want in the C program
* specification is done by writing C programs with assertions that can
  then be proved reachable or otherwise
* they deal with the finite bound not being big enough by using an
  unwinding assertion - how could something like that be added to TESLA?
* so specification of hardware using C that is translated into a
  simplified SSA form, then converted to a bit vector equation

* so the CBMC paper I had already is really a summary of the longer
  technical report from 2003 (with a focus on the GUI side of things ot
  market it as a usable tool?)

* next paper is MOPS - different authors (this time out of berkeley)
* MOPS is cited in the initial TESLA paper as a similar work, but the
  difference is called out as being predicated on return values and
  parameters - this is a useful thing to note as an improvement I
  contribute
* similar ideas, however - MOPS represents its properties as automata
  from the beginning
* definitely less focus on having the programmer instrument their own
  code - paper focuses on 5 hand-picked assertions that they check
* lack of description on how they actually implemented the tool -
  mention of pushdown automata as an implementation technique, but not
  much beyond that
* assertions are not inline to the program they assert over
* lack of implementation is possibly because the paper I'm looking at is
  an application of MOPS to large bodies of code

* MOPS implementation paper - gives a bit more detail on how MOPS is
  implemented. the key idea is that they use a pushdown automaton to
  represent program traces (equiv. to a context free language).
* technique isn't bounded model checking (ideas popped up around the
  same times by the look of it)

* LLBMC uses broadly the same ideas as CBMC, but applies them to LLVM IR
  rather than to C programs in source form (idea is that translation to
  a boolean formula will probably be easier because the semantics of
  LLVM are simpler than those of C).
* using LLVM means being able to support C++ (and indeed any language
  that compiles to LLVM)
* properties checked are similar to those checked by CBMC (but better at
  it because of the use of LLVM)

* a couple more references from the original TESLA paper mention aspect
  oriented debugging tools (AWED, SPOX) - what are these?
* aspect oriented programming is the idea that you separate concerns
  when programming (e.g. all security code in one place, all logging in
  another)
* hamlen, jones focus on security properties, also expressed as automata
* define an automaton that *only* accepts event sequences that are valid
  with respect to a security policy
* they give a formal semantics of SPoX, and an implementation that can
  interpose code in an aspect-oriented way based on these automata
* other paper on aspect-oriented again focuses on Java - idea is that
  debugging can be made easier with pointcut style interposition. also
  looks a lot at distributed systems, causality etc
* second paper less similar to TESLA
