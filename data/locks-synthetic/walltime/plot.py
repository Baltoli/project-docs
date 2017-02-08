#!/usr/bin/env python3

import sys

def get_mean_stdev(lines):
    return list(map(lambda s: float(s.strip()), lines[1].split(",")))

if __name__ == "__main__":
    version = str(sys.argv[1])
    min_threads = int(sys.argv[2])
    max_threads = int(sys.argv[3])
    step = int(sys.argv[4])
    nsort = int(sys.argv[5])
    for n in range(min_threads, max_threads + 1, step):
        with open("{}_{}_{}".format(version, n, nsort)) as f:
            print([n] + get_mean_stdev(f.readlines()))
