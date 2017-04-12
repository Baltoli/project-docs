# Defensively Coded Library

TESLA can be used to enforce invariants of some library code (for example, that
a log file is opened at most once during a response handler, and is closed
afterwards).

The idea is for the library to expose a limited interface against which a client
/ plugin can be written - exposing TESLA-checked functions that cannot be
misused. From my initial stabs at this so far, the things that TESLA is going to
be best at enforcing are resource management issues (the kind of thing you'd be
able to do with RAII in C++).

Idea: implement a networked key-value store that provides some kind of a plugin
interface (i.e. most of the implementation is library code, except for a few
components that the user can supply - together they build a full app). Key-value
store is actually arbitrary - command interface! Client supplies their handler
function, and the library gives them access to some useful things (a statistics
structure, a log file, whatever else I can think of).

So the library needs to provide everything except a handler function, which is
supplied as handler.c.
