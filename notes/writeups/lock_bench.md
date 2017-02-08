# Lock Benchmarking

We would like to produce a benchmark that performs real work for a
reasonably long period of time, and generates a suitable level of
contention on a lock. This benchmark can then be used to demonstrate the
benefits of static analysis and optimisation on an example program.

## Basic Setup

We will have a large number of threads, each of which will perform a
chunk of work *with a lock held*. The total runtime of the program will
be compared between the statically-optimised version and the
TESLA-instrumented version.

The benchmark chosen is an interval bubble sort. Each thread is
responsible for sorting an interval of a global array, and for checking
that it's sorted at the end. The number of threads and the size of the
data array are the important parameters in this benchmark.

## Results

Next step now that I have a script for gathering data is to actually get
some significant results that I can present. Would be good to
demonstrate the effects of increasing contention on the lock
performance.
