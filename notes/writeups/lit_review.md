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
  path formula (E[f]) by proving it for some finite bound k.
* 
