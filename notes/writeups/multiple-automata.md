# Multiple Automata

## Problem

In developing the set of small experimental programs that demonstrate
features of the lock automata, I found that in some cases it was not
possible to have multiple lock structures instrumented with the same
automata (e.g. `acq_rel`).

Robert suggested in a meeting that there is a map of assertion
parameters to distinct automaton instances somewhere in the runtime.

## Minimum Working Example

The lock examples are too big to be usefully diagnosable. I should
therefore develop a minimum example that demonstrates the problem.

MWE is in `experiments/multiple_automata`.

## Strict Mode

I think the problem possibly comes from my misunderstanding of strict
mode. From the docs, an event named in a strict mode automaton can
*only* occur within the scope of that automaton. For example, in the MWE
experiment above, the automaton `my_auto` names events `call(...)` etc.
These events can only occur within the scope of the automaton (i.e. the
code path that includes a 'now' event for that automaton).

In the simple example I've written, there is only one code path - the
one that goes through `main` via calls to the `init` and `end`
functions. This means that even in conditional mode, the events need to
happen *exactly* as described.

Basically, the point is that the events shouldn't be occurring at all if
they are named in an explicit automata. The assertions need to describe
exactly how the events happen within the context.

This is why I was seeing those issues with locking and unlocking of a
second lock in the locks experiment - the `acq_rel` automaton needs
there to be no other acquire or release events at all within the scope
in which it is used. This is why using a second lock without declaring
it as being used with an automaton causes problems.

The moral is that for event 'A' inside an explicit automata, if that
event happens anywhere it must do so in the way the automata prescribes.
In conditional mode, 'A' can occur elsewhere, as long as it is on a
different execution path to the assertion site where it is mentioned.
