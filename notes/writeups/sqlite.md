# SQLite

Looking to pick a piece of software that I can add TESLA instrumentation to in
order to demonstrate performance characteristics of instrumented /
uninstrumented code.

Reasons for choosing SQLite as a first example:
* Designed to be simple to compile - distributed as 180000 lines of C in a
  single file. This should in theory mean that TESLA instrumentation can be
  added easily (as setting up a build isn't trivial).
* Lots of code to look at - it's a big library with a lot of complex features
  that might benefit from being instrumented.

Worth noting that there's a downside to picking SQLite - it's unlikely that I
will find any actual bugs in the code as it's so comprehensively tested. That
said, it's still probably a good example of code that can be used with TESLA.

An alternative option is to use a smaller library (e.g. one of the many single
file C libraries available), where I'd be more likely to find bugs etc, but less
likely to have code suitable for TESLA instrumentation.

## Setup

The process has been pretty easy because of how simple SQLite is to build - I've
essentially ended up grafting on a bunch of rules that build the TESLA files as
appropriate from the SQLite sources.
