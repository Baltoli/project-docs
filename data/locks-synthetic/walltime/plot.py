#!/usr/bin/env python2

import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
import seaborn as sns

def get_mean_stdev(lines):
    return list(map(lambda s: float(s.strip()), lines[1].split(",")))

if __name__ == "__main__":
    versions = ["instrumented", "static"]
    min_threads = int(sys.argv[1])
    max_threads = int(sys.argv[2])
    step = int(sys.argv[3])
    nsort = int(sys.argv[4])
    data = {}
    for version in versions:
        data[version] = []
        for n in range(min_threads, max_threads + 1, step):
            with open("{}_{}_{}".format(version, n, nsort)) as f:
                data[version].append([n] + get_mean_stdev(f.readlines()))

    ixs = map(lambda d: d[0], data["instrumented"])
    iys = map(lambda d: d[1], data["instrumented"])
    ierrs = map(lambda d: d[2], data["instrumented")

    sxs = map(lambda d: d[0], data["static"])
    sys = map(lambda d: d[1], data["static"])
    serrs = map(lambda d: d[2], data["static"])
    
    plt.xlim(xmin=0, xmax=max(ixs[-1], sxs[-1]) + step)
    plt.ylim(ymin=0, ymax=max(iys[-1], sys[-1]) + 2)
    
    plt.scatter(ixs, iys, zorder=2)
    plt.errorbar(ixs, iys, yerr = ierrs, linestyle='None', zorder=1)
    
    plt.scatter(sxs, sys, zorder=2)
    plt.errorbar(sxs, sys, yerr = serrs, linestyle='None', zorder=1)

    plt.xlabel('No. of concurrent threads')
    plt.ylabel('Mean runtime (s)')
    plt.savefig("{}_{}.eps".format(version, nsort), format='eps', dpi=1000)
