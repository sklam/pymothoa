import logging
#logging.basicConfig(level=logging.DEBUG)

from mamba.compiler import function
from mamba.types import *
from mamba.dialect import *

@function(ret=Float, args=[ [Float], Int])
def test_array(A, N):
    var ( temp = Float )
    temp = 0
    for i in xrange(N):
        temp = temp + A[i]
    return temp


@function(ret=Float, args=[ [Float], Int])
def test_array2(A, N):
    var ( result = Float,
          temp   = Float,
          Stride = Int,   )
    result = 0
    Stride = 8
    for i in xrange(N-Stride):
        temp = 0
        for s in xrange(Stride):
            temp = temp + A[i+s]
        result = result + temp
    return temp

# -------------------------------------------------------------------

import unittest
from random import random
from numpy import array
from ctypes import c_float
from _util import benchmark, relative_error, benchmark_summary

class Test(unittest.TestCase):
    def setUp(self):
        self.N = 1000
        self.A = array(map(lambda _: random()+1, range(self.N)), dtype=c_float)
        self.REP = 100

    def test_array(self):
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_array(self.A, self.N)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_array.jit(self.A, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_array2(self):
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_array(self.A, self.N)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_array.jit(self.A, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    if True:
        print 'Assembly'.center(80, '=')
        print test_array2.assembly()
        print 'End Assembly'.center(80, '=')

    benchmark_summary()



