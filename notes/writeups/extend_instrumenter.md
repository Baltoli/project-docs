# Instrumenter Extension

We want to extend the instrumenter so that it knows about the `deleted`
field, and will take the appropriate action when it is encountered (i.e.
to not add the instrumentation to the module).

## Detection

A `tesla::Automaton` has a `Usage` associated with it. Detecting a
deleted usage can be done through this I think.

## Deletion

What is the best way to prevent the instrumentation from being added?
The core implementation of the instrumenter is a collection of LLVM
passes that run on the module, replacing the appropriate events with
instrumentation code.

I *think* the one we're interested in here is the
`AssertionSiteInstrumenter`. It seems to replace the dummy function
calls with the appropriate instrumentation code, so I think that if we
hook in here then we can stop the code from ever being added to the
module.

In fact, we have to check for deleted usages in all of the four passes.
Simple testing seems to indicate that we can just skip over loop
iterations for deleted usages (maybe this will cause a subtle bug down
the line, but I hope not).
