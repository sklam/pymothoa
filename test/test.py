
import logging
#logging.basicConfig(level=logging.DEBUG)

from mamba.compiler import function
from mamba.types import *
from mamba.dialect import *

@function(ret=Int)
def test_constant():
    var (
        A = Int,
        B = Int,
        C = Int,
    )
    A = (123 + 321)*2
    B = 9
    C = A * B
    return C

@function(ret=Int, args=[Int])
def test_arg(B):
    var (
        A = Int,
        C = Int,
    )
    A = (123 - 321)*2
    C = A / B
    return C

@function(ret=Int, args=[Int])
def test_call(a):
    return test_arg(a)

@function(ret=Int, args=[Int])
def test_recur(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur(a-1)

@function(ret=Int64, args=[Int64])
def test_recur64(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur64(a-1)

@function(ret=Float, args=[Float])
def test_float(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_float(a/1.1)

@function(ret=Double, args=[Double])
def test_double(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_double(a/1.1)

@function(ret=Int, args=[Int, Int])
def test_forloop(val, repeat):
    for i in xrange(3, repeat):
        val = val + i
    return val


# -------------------------------------------------------------------

import unittest
from random import random, randint
from numpy import array
from ctypes import c_float
from _util import benchmark, relative_error, benchmark_summary

class Test(unittest.TestCase):
    def setUp(self):
        self.REP = 512

    def test_constant(self):

        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_constant()

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_constant.jit()

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_arg(self):
        ARG = randint(1,0xffffffff)
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_arg(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_arg.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


    def test_call(self):
        ARG = randint(1,0xffffffff)
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_call(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_call.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_recur(self):
        ARG = randint(1,100)
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_recur(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_recur.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


    def test_recur64(self):
        ARG = randint(1,100)
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_recur64(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_recur64.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_float(self):
        ARG = 321.321e+2
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_float(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_float.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_double(self):
        ARG = 321.321e+4
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_double(ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_double.jit(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_forloop(self):
        ARG = 1, 2**10
        with benchmark('Python', 'LLVM') as (timer_py, timer_jit):
            with timer_py:
                for _ in xrange(self.REP):
                    py_result = test_forloop(*ARG)

            with timer_jit:
                for _ in xrange(self.REP):
                    jit_result = test_forloop.jit(*ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    benchmark_summary()

