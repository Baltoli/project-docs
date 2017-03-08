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

### Server Spec

The server sets up a socket, binds to an address etc. It then runs a main loop
where it accepts connections from clients and spawns off a thread that does
something with the file descriptor for the connection.

Now we want to write the actual server code.

### Client Spec
