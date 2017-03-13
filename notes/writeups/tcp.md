# TCP Implementation

A potential candidate for a larger piece of software to instrument using TESLA,
then analyse statically to determine performance gains is a TCP implementation.
The primary benefit to doing this work on TCP is that the protocol looks a lot
like a state machine internally - TESLA can probably be used effectively inside
the implementation to show that the appropriate transitions are taken.
Preliminary work on the client-server implementation seems to indicate that
validating a network protocol in this way with TESLA is a) viable and b)
possible to demonstrate performance improvements on.

At the outset of the project, one idea had been to try and instrument the
FreeBSD TCP implementation with TESLA. For a number of reasons, I don't think
this is especially viable. Even accounting for the difficulty involved in
writing a protocol implementation, I think a from-scratch implementation will be
a better idea than trying to wrangle the FreeBSD implementation.

## Basic Idea

FreeBSD (like Linux) has the ability to create virtual network interfaces
through the TUN / TAP mechanism, allowing for user-mode network devices to be
implemented. The TCP/IP implementation I'm proposing here will be a TUN device -
once set up (as I understand it), it will have a file descriptor exposed that
can be used to read / write single packets.

## Artefacts

The primary outcome of doing this work is a TESLA-instrumented, user-mode TCP
implementation. This will be able to (ideally) act like a regular TCP socket, at
least to a first approximation.

Once implemented, having TCP exposed means that performance benchmarks can be
more easily carried out - normal applications should in theory be able to use
the virtual device to send and receive data.

## Vs. LWIP

There are pros and cons of self-implementing TCP when compared to an existing
library such as LWIP.

For LWIP:

* Avoids lots of "busy-work" related to stuff like packet parsing and
  construction that isn't so relevant to the task at hand (instrumentation using
  TESLA).
* Robert suggested that this might be seen more positively in the writeup -
  instrumenting a real piece of software is perhaps a more useful task, rather
  than reinventing the wheel.
* Is much more likely to expose flaws in my model checking procedures caused by
  real code (as when coding myself, it's likely that I'll end up compensating in
  the code itself - rather than improving the model checker).

For my own implementation:

* Will be conceptually simpler from my perspective - I will have full control
  over the abstractions and coding style used.
* Integration with TESLA is trivial.

On the basis of these comparisons, I think it will probably end up being the
better approach to use LWIP - implementing TCP/IP is a fun project for another
time I think.

## Using LWIP

LWIP is distributed as a library (note that this means we're in control of how
things get compiled, as it's designed to be portable etc). Then, a client
application is responsible for integrating LWIP into their app using the LWIP
API.

A useful first step might be to try to get LWIP compiling as a library (i.e.
prod it and see what happens to the build process).
