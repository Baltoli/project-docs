#!/usr/bin/env python2

import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
import seaborn as sns
import csv
import os

if __name__ == "__main__":
    path = sys.argv[1]

    xs = []
    ys = []
    with open(path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            xs.append(row[0])
            ys.append(row[1])

    plt.xlabel('No. of instructions in each trace')
    plt.ylabel('Runtime (s)')
    
    plt.ylim(ymin=0, ymax=float(max(ys)))
    plt.scatter(xs[1:-1], ys[1:-1])

    fig = '.'.join(path.split('.')[:-1])
    plt.savefig("{}.eps".format(fig), format='eps', dpi=1000)
