#!/usr/bin/env python2

import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
import seaborn as sns

def get_mean_stdev(lines):
    return list(map(lambda s: float(s.strip()), lines[1].split(",")))

if __name__ == "__main__":
    version = str(sys.argv[1])
    min_threads = int(sys.argv[2])
    max_threads = int(sys.argv[3])
    step = int(sys.argv[4])
    nsort = int(sys.argv[5])
    data = []
    for n in range(min_threads, max_threads + 1, step):
        with open("{}_{}_{}".format(version, n, nsort)) as f:
            data.append([n] + get_mean_stdev(f.readlines()))
    xs = map(lambda d: d[0], data)
    ys = map(lambda d: d[1], data)
    errs = map(lambda d: d[2], data)
    plt.xlim(xmin=0, xmax=xs[-1] + step)
    plt.ylim(ymin=0, ymax=ys[-1] + 2)
    plt.errorbar(xs, ys, yerr = errs, linestyle='None', zorder=1)
    plt.scatter(xs, ys, zorder=2)
    plt.scatter(map(lambda x:x-1, xs), ys, zorder=3)
    plt.xlabel('No. of concurrent threads')
    plt.ylabel('Mean runtime (s)')
    plt.savefig("{}_{}.eps".format(version, nsort), format='eps', dpi=1000)
