# Copyright (c) 2012, Siu Kwan Lam
# All rights reserved.

from time import time
import inspect
from contextlib import contextmanager

BENCHMARK_SUMMARY = []

class Timer:
    def start(self):
        self._start = time()

    def stop(self):
        self._stop = time()

    def duration(self):
        return self._stop - self._start

    def __enter__(self, *args, **kwargs):
        self.start()

    def __exit__(self, *args, **kwargs):
        self.stop()


def benchmark_summary():
    print
    print 'Benchmark Summary'.center(80, '=')
    for bm in BENCHMARK_SUMMARY:
        print
        print bm.name

        # sort entries by duration
        sorted_entries = sorted((timer.duration(), entry)
                                for entry, timer in bm.entries.items())

        fastest = sorted_entries[0]

        print '\tFastest entry is', fastest[1]

        fastest_dt = fastest[0]
        for dt, name in sorted_entries:
            speedup = dt / fastest_dt
            print '\t%.2fx speedup over %s (%.2gs)'%(speedup, name, dt)

    print '='*80
    print

def relative_error(expect, got):
    expect = float(expect)
    got = float(got)
    return abs(got-expect)/(expect+1e-30)

class Benchmark:
    def __init__(self, name):
        self.name = name
        self.entries = {}

    @contextmanager
    def entry(self, name):
        if name in self.entries:
            raise NameError(name, 'repeated')
        else:
            timer = self.entries[name] = Timer()
            timer.start()
            yield timer
            timer.stop()

    def times(self, names):
        line = []
        for name in names:
            timer = self.entries[name]
            dt = timer.duration()
            line.append(dt)
        return line

    def names(self):
        return [entry for entry in self.entries.keys()]

@contextmanager
def benchmark(title=''):
    FRAME = inspect.currentframe().f_back.f_back
    CALLER = FRAME.f_code
    name = '%s at %s:%d'%(title, CALLER.co_name, FRAME.f_lineno)
    bm = Benchmark(name)
    yield bm
    BENCHMARK_SUMMARY.append(bm)

