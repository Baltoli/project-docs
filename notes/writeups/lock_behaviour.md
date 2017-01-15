# Lock Behaviour

As part of my initial work trying to get some TESLA assertions working,
I've implemented an automaton that checks lock acquisition and release
properties. In order to statically analyse this automaton, I need to
fully specify the locking properties that it enforces of a program.

## Strict Mode

Because of strict mode, the automaton usages need to fully specify the
locking behaviour on *every* code path. That is, every lock operation
performed needs to be accounted for by an automaton - there can be no
unwatched lock operations.

This means that any change in locking behaviour will break assertions -
informally, things like taking out another lock or not using a lock
declared as being used will do this.

## Informal Specification

The locks modelled in this experiment are simple mutual exclusion locks
that can be held by a single consumer at a time. The locking interface
is through four functions:

```
void lock_init(lock_t *);
void lock_free(lock_t *);
bool lock_acquire(lock_t *);
void lock_release(lock_t *);
```

The acquire function for a particular lock type will return `false` if
the lock could not be acquired (i.e. it is already held by another
consumer), and `true` if the acquisition succeeded. This allows threads
to spin on a lock until it becomes available, then to enter their
critical section.

The automaton is designed to enforce proper locking discipline on users
of these locks - for example, it is incorrect to attempt to acquire a
lock after it has already been acquired, to release it again after
release, or to release before acquiring. This is expressed by the
`acq_rel` automaton as the lock having a sequence of 0 or more `false`
returns, then a single call to the release function. As described above,
strict mode means that any other lock events will cause the assertions
to fail (even those that reference other locks to the one being
mentioned by the `acq_rel` instance).

## Examples Written

In an early attempt to specify the behaviour of these locks, I've
written a number of example programs that describe one aspect of the
lock's behaviour when it is described by `acq_rel`. These examples are
written using mocked locks that behave in a predictable way on a single
thread. They exist in the TSA repository in `experiments/locks`.

* **basic**: The lock is spun on until acquired, then released. There is
  no error as the behaviour is correct.
* **mult_acq**: A call to `lock_acquire` is made after the spin section
  ends. There is an error as the sequence of returns is then `...FFFTF`.
* **mult_rel**: The lock is released more than once. There is an error
  because of the extra lock event not described by the automaton.
* **no_acq**: The lock is not acquired and so there is an error.
* **no_rel**: The lock is not released within the automaton bounds,
  and so there is an error.
* **no_acq_rel**: The lock is neither acquired nor released, so there is
  an error.
* **other**: The lock is acquired and released correctly, but so is
  another lock. There is an error as the other lock causes more events
  to be generated that are not described by the automaton.

## Formal Specification
