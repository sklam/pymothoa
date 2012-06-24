import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Float, args=[ Array(Float), Int])
def test_array(A, N):
    var ( temp = Float )
    temp = 0
    for i in xrange(N):
        temp = temp + A[i]
    return temp

test_array_py = test_array.run_py

@function(ret=Float, args=[ Array(Float), Int])
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

test_array2_py = test_array2.run_py

@function(args=[ Array(Float), Int ])
def test_array_reverse(A, N):
    var ( temp = Array(Float, N) )
    for i in xrange(N):
        temp[i] = A[i]
    for j in xrange(N):
        A[j] = temp[(N-1)-j]

# -------------------------------------------------------------------

import unittest
from random import random
import numpy as np
import array
from ctypes import c_float
from _util import benchmark, relative_error, benchmark_summary

class Test(unittest.TestCase):
    def setUp(self):
        self.N = 512
        self.B = map(lambda _: random()+1, range(self.N))
        self.A = np.array(self.B, dtype=c_float)
        self.C = array.array('f', self.B)
        self.REP = 512

    def test_array(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_array_py(self.A, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_array(self.A, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_array_from_list(self):
        # This is extremely slow!
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_array_py(self.B, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_array(self.B, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_array_from_array(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_array_py(self.C, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_array(self.C, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_array2(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_array_py(self.A, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_array(self.A, self.N)

        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_array_reverse_numpy(self):
        # numpy array
        data_reversed = list(reversed(self.A))
        test_array_reverse(self.A, self.N)
        for i, j in zip(data_reversed, self.A):
            self.assertTrue(i==j)

        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    data_reversed = list(reversed(self.A))

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    test_array_reverse(self.A, self.N)

    def test_array_reverse_array(self):
        # array.array
        data_reversed = list(reversed(self.C))
        test_array_reverse(self.C, self.N)
        for i, j in zip(data_reversed, self.C):
            self.assertTrue(i==j)

        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    data_reversed = list(reversed(self.C))

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    test_array_reverse(self.C, self.N)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    if False:
        print 'Assembly'.center(80, '=')
        print test_array2.assembly()
        print 'End Assembly'.center(80, '=')

    benchmark_summary()
