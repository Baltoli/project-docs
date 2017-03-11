# Server

Want to write a program that:

* Does something useful
* Can be instrumented using TESLA on a hot code path

A possible candidate for this is some kind of multithreaded server - it would
accept connections (one per thread), then do some kind of work with the
connection. The work can then be instrumented using TESLA.

## Basic Structure

The core of this app will be a main loop that listens for connections, accepts
them if they arrive, then spawns a thread for each connection and does some
work.

## Ideas

* One thing that might be interesting to implement is a simple network protocol
  of some kind, then use TESLA to make sure that it all behaves properly.

## Network Protocol

Build a simple network protocol on top of a TCP connection. Will look like a
really tiny verified delivery protocol. Flow is:

* Client will first send a request packet that specifies how many packets they
  want to send. 
* The server then acknowledges the request.
* Client sends each of their data packets to the server and waits for a reply
  before sending the next.
* Finally, the client sends a 'done' packet, and the server replies with the
  same.

This all looks a bit like a state machine.

The different types of packet we require are:

* Request (client -> server)
* Permit (server -> client)
* Data (client -> server)
* Ack (server -> client)
* Done (server <-> client)

Let's encode packets as a small fixed size for simplicity (say 8 bytes):

```
-------------------------------------------------
|  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |
|-----------------------------------------------|
|type |    sn     |         data                |
-------------------------------------------------
```

So the first byte of the packet encodes the type, the second and third are the
sequence number as a 16-bit integer, and the remaining five are data.

* For request and permit, the sequence number should hold the number of packets
  the client wants to send.
* For data and ack, the sequence number gets incremented as expected. Data
  packets have their data in the five-byte area, while ack packets should zero
  it.
* Done packets should be zero except for the type.

## State Machines & TESLA

The current implementation of the client and server are neat from a
software-engineering perspective - they both speak the same protocol so can both
have the same interface, and are then implemented in terms of packet handlers.
This means that the control flow through the implementation is *data-dependent*
(nothing is known statically about the control flow other than that the generic
packet handler can call each other possible handler with the appropriate
arguments).

TESLA is well suited to instrumenting this sort of thing, but to combine it with
static analysis we need to make the idea of a state machine much more explicit.
For example, the state diagram for the server looks something like:
```
             initial
                +
                |
                v
  +------+expect_request
  v             +
error           |   +----+
  ^             v   v    |
  +------+expect_data    |
                +   +    |
                |   +----+
                v
            +---+--+
            | done |
            +------+
```
In the current implementation, this is encoded dynamically when we would like it
to be encoded statically. Then, TESLA assertions could be used to validate the
transitions that the system undergoes statically (to make sure, for example,
that `expect_request` is only ever called from the initial state).

The potential issue that this design has is blowing the stack - if there is a
loop in the state diagram then it's possible that recursion depth is reached and
things go wrong. I think that this can be handled by careful design of the state
space, compiler optimisations, or converting recursive loops to iterative ones.

Current status is that the server implementation tends to segfault *a lot* under
load (but also that adding a bunch of TESLA assertions did seem to make it slow
down a bit).

Now should look at the explicit-state version.
