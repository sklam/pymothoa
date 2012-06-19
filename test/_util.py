from time import time
import inspect
from contextlib import contextmanager

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

@contextmanager
def benchmark(name1, name2):
    CALLER = inspect.currentframe().f_back.f_back.f_code

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

BENCHMARK_SUMMARY = []

def benchmark_summary():
    print
    print 'Benchmark Summary'.center(80, '=')
    for m in BENCHMARK_SUMMARY:
        print m
    print '='*80

def relative_error(expect, got):
    expect = float(expect)
    got = float(got)
    return abs(got-expect)/expect

def test_and_compare(fn, *args):
    R = 200

    ret_llvm = fn.jit(*args)
    s = time()
    for i in xrange(R):
        ret_llvm = fn.jit(*args)
    e = time()
    print 'llvm: ', ret_llvm

    t_llvm = e-s


    s = time()
    for i in xrange(R):
        ret_python = fn(*args)
    e = time()
    print 'python:', ret_python

    t_python = e-s

    relative_error = float(abs(ret_llvm-ret_python))/ret_python

    if relative_error > 1e-5:
        print 'relative_error =', relative_error
        raise ValueError('Computation error!')

    if t_llvm < t_python:
        print 'LLVM is faster by %f seconds (%.1fx)'%(
            t_python-t_llvm,
            t_python/t_llvm,
            )
    elif t_python < t_llvm:
        print 'Python is faster by %f seconds (%.2fx)'%(
            t_llvm-t_python,
            -t_llvm/t_python,
            )

