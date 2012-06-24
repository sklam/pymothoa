
import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
from pymothoa.types import *
from pymothoa.dialect import *

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

test_constant_py = test_constant.run_jit

@function(ret=Int, args=[Int])
def test_arg(B):
    var (
        A = Int,
        C = Int,
    )
    A = (123 - 321)*2
    C = A / B
    return C

test_arg_py = test_arg.run_py

@function(ret=Int, args=[Int])
def test_call(a):
    return test_arg(a)

def test_call_py(a):
    return test_arg_py(a)

@function(ret=Int, args=[Int])
def test_recur(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur(a-1)

def test_recur_py(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur_py(a-1)

@function(ret=Int64, args=[Int64])
def test_recur64(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur64(a-1)

def test_recur64_py(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur64_py(a-1)

@function(ret=Float, args=[Float])
def test_float(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_float(a/1.1)

def test_float_py(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_float_py(a/1.1)

@function(ret=Double, args=[Double])
def test_double(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_double(a/1.1)

def test_double_py(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_double_py(a/1.1)

@function(ret=Int, args=[Int, Int])
def test_forloop(val, repeat):
    for i in xrange(3, repeat):
        val = val + i
    return val

test_forloop_py = test_forloop.run_jit
# -------------------------------------------------------------------

import unittest
from random import random, randint
from numpy import array
from ctypes import c_float
from _util import benchmark, relative_error, benchmark_summary

class Test(unittest.TestCase):
    def setUp(self):
        self.REP = 1000

    def test_constant(self):

        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_constant_py()

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_constant()

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_arg(self):
        ARG = randint(1,0xffffffff)
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_arg_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_arg(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


    def test_call(self):
        ARG = randint(1,0xffffffff)
        with benchmark() as bm:
            with bm.entry('Python'):
                    py_result = test_call_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_call(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_recur(self):
        ARG = randint(1,100)
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_recur_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_recur(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


    def test_recur64(self):
        ARG = randint(1,100)
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_recur64_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_recur64(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_float(self):
        ARG = 321.321e+2
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_float_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_float(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_double(self):
        ARG = 321.321e+4
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_double_py(ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_double(ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)

    def test_forloop(self):
        ARG = 1, 2**10
        with benchmark() as bm:
            with bm.entry('Python'):
                for _ in xrange(self.REP):
                    py_result = test_forloop_py(*ARG)

            with bm.entry('JIT'):
                for _ in xrange(self.REP):
                    jit_result = test_forloop(*ARG)

        self.assertTrue(relative_error(py_result, jit_result) < 0.0001/100)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    benchmark_summary()
