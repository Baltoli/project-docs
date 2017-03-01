#!/usr/bin/env python3
from subprocess import Popen, PIPE
import sys
import statistics
import os

HOME = os.getenv("HOME")
TESLA_BUILD = os.path.join(HOME, "tesla-static-analysis/build/tesla/")
TESLA_MODEL = os.path.join(TESLA_BUILD, "model/tesla-model")

EXPERIMENTS = os.path.join(HOME, "tesla-static-analysis/build/experiments/locks")

def experiment_file(name, ext=None):
    return os.path.join(EXPERIMENTS, name + ("." + ext if ext else ""))

def get_wall_time(prog, bc, m, depth):
    p = Popen(
        ["/usr/bin/time", "-p", prog, str(bc), str(m), "-bound="+str(depth)], 
        stdout=PIPE,
        stderr=PIPE
    )

    o, e = p.communicate()
    line = str(e).split('\\n')[0]
    val = line.split(' ')[-1]
    return float(val)

if __name__ == "__main__":
    exp = sys.argv[1]
    runs = 5 if len(sys.argv) < 3 else int(sys.argv[2])

    bitcode = experiment_file(exp, "bc")
    manifest = experiment_file(exp, "manifest")

    results = []
    max_len = 15
    start = 1
    for le in range(start, start+max_len):
        print("Running at {}".format(le*100), file=sys.stderr)
        times = []
        for i in range(runs):
            val = get_wall_time(TESLA_MODEL, bitcode, manifest, le*100)
            times.append(val)
        results.append(times)
    
    for ind, row in enumerate(results):
        print("{},{:.2f},{:.2f}".format(
            (ind+start)*100, 
            statistics.mean(row),
            statistics.stdev(row)
        ))
