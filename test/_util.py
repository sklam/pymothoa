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
        fastest_dt = None
        for entry, timer in bm.entries.items():
            dt = timer.duration()
            print '\t-', entry, '%.2gs'%dt
            if fastest_dt is None or dt < fastest_dt:
                fastest_dt = dt
                fastest_entry = entry
        print '\tFastest entry is', fastest_entry
        for entry, timer in bm.entries.items():
            if entry != fastest_entry:
                dt = timer.duration()
                speedup = dt / fastest_dt
                print '\t%.2fx speedup over %s'%(speedup, entry)

    print '='*80
    print

def relative_error(expect, got):
    expect = float(expect)
    got = float(got)
    return abs(got-expect)/expect

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


@contextmanager
def benchmark():
    CALLER = inspect.currentframe().f_back.f_back.f_code
    name = '%s:%d'%(CALLER.co_name, CALLER.co_firstlineno)
    bm = Benchmark(name)
    yield bm
    BENCHMARK_SUMMARY.append(bm)

    '''
    t1 = Timer()
    t2 = Timer()
    yield t1, t2

    dt1 = t1.duration()
    dt2 = t2.duration()

    name = '%s:%d'%(CALLER.co_name, CALLER.co_firstlineno)
    template = '%30s | %%s is faster by %%.1fx' % name

    if dt1 < dt2:
        msg = template % (name1, dt2/dt1)
    else:
        msg = template % (name2, dt1/dt2)

    BENCHMARK_SUMMARY.append(msg)
    '''
