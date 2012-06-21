import logging
#logging.basicConfig(level=logging.DEBUG)

from mamba.compiler import function
from mamba.types import *
from mamba.dialect import *

VW = 4

@function(ret=Float, args=[ [Float], Int])
def test_vector_float(A, N):
    var (
      temp   = Vector(Float, VW),
      acc    = Vector(Float, VW),
      result = Float,
    )

    acc[0] = 0
    acc[1] = 0
    acc[2] = 0
    acc[3] = 0

    for i in xrange(N/VW):
        temp[0] = A[i*VW + 0]
        temp[1] = A[i*VW + 1]
        temp[2] = A[i*VW + 2]
        temp[3] = A[i*VW + 3]
        acc = acc + temp

    return acc[0] * acc[1] * acc[2] * acc[3]


@function(ret=Double, args=[ [Double], Int])
def test_vector_double(A, N):
    var (
      temp   = Vector(Double, VW),
      acc    = Vector(Double, VW),
      result = Double,
    )

    acc[0] = 0
    acc[1] = 0
    acc[2] = 0
    acc[3] = 0

    for i in xrange(N/VW):
        temp[0] = A[i*VW + 0]
        temp[1] = A[i*VW + 1]
        temp[2] = A[i*VW + 2]
        temp[3] = A[i*VW + 3]
        acc = acc + temp

    return acc[0] * acc[1] * acc[2] * acc[3]


@function(ret=Int, args=[ [Int], Int])
def test_vector_int(A, N):
    var (
      temp   = Vector(Int, VW),
      acc    = Vector(Int, VW),
      result = Int,
    )

    acc[0] = 0
    acc[1] = 0
    acc[2] = 0
    acc[3] = 0

    for i in xrange(N/VW):
        temp[0] = A[i*VW + 0]
        temp[1] = A[i*VW + 1]
        temp[2] = A[i*VW + 2]
        temp[3] = A[i*VW + 3]
        acc = acc + temp

    return acc[0] * acc[1] * acc[2] * acc[3]


def test_vector_py(A, N):
    accX = 0
    accY = 0
    accZ = 0
    accW = 0

    for i in xrange(N/VW):
        accX += A[i*VW + 0]
        accY += A[i*VW + 1]
        accZ += A[i*VW + 2]
        accW += A[i*VW + 3]

    return accX * accY * accZ * accW

# -------------------------------------------------------------------

import unittest
from random import random, randint
from numpy import array
from ctypes import c_double, c_float, c_int
from _util import benchmark, relative_error, benchmark_summary

class Test(unittest.TestCase):

    def setUp(self):
        self.N = VW*512
        self.Af = array(map(lambda _: random()+1, xrange(self.N)), dtype=c_float)
        self.Ad = array(map(lambda _: random()+1, xrange(self.N)), dtype=c_double)
        self.Ai = array(map(lambda _: randint(1, 0xffff), xrange(self.N)), dtype=c_int)
        self.REP = 100

    def test_vector_float(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_vector_py(self.Af, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_vector_float(self.Af, self.N)

            print py_result, jit_result
        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_vector_double(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_vector_py(self.Ad, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_vector_double(self.Ad, self.N)

            print py_result, jit_result
        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

    def test_vector_int(self):
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_vector_py(self.Ai, self.N)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_vector_int(self.Ai, self.N)

            print py_result, jit_result
        self.assertTrue(relative_error(py_result, jit_result) < 0.01/100)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    if True:
        print 'Assembly'.center(80, '=')
        print test_vector_double.assembly()
        print 'End Assembly'.center(80, '=')

    benchmark_summary()



