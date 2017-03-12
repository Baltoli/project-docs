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
