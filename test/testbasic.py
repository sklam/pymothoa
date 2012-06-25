
import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
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

@function(ret=Int, args=[Int, Int])
def test_ifelse(A, B):
    if A == B:
        return 1
    elif A > B:
        return 2
    else:
        return 3

test_ifelse_py = test_ifelse.run_py

default_module.optimize()
# -------------------------------------------------------------------

import unittest
from random import random, randint
from numpy import array
from ctypes import c_float
from pymothoa.util.testing import relative_error

class Test(unittest.TestCase):
    def test_constant(self):
        py_result = test_constant_py()
        jit_result = test_constant()

        self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_arg(self):
        for _ in xrange(0, 100):
            ARG = randint(1,0xffffffff)
            py_result = test_arg_py(ARG)
            jit_result = test_arg(ARG)
            self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_call(self):
        for _ in xrange(0, 100):
            ARG = randint(1,0xffffffff)
            py_result = test_call_py(ARG)
            jit_result = test_call(ARG)

            self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_recur(self):
        for _ in xrange(0, 100):
            ARG = randint(1,100)
            py_result = test_recur_py(ARG)
            jit_result = test_recur(ARG)

            self.assertLess(relative_error(py_result, jit_result), 0.0001/100)


    def test_recur64(self):
        for _ in xrange(0, 100):
            ARG = randint(1,100)
            py_result = test_recur64_py(ARG)
            jit_result = test_recur64(ARG)

            self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_float(self):
        ARG = 321.321e+2
        py_result = test_float_py(ARG)
        jit_result = test_float(ARG)

        self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_double(self):
        ARG = 321.321e+4
        py_result = test_double_py(ARG)
        jit_result = test_double(ARG)

        self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_forloop(self):
        ARG = 1, 2**10
        py_result = test_forloop_py(*ARG)
        jit_result = test_forloop(*ARG)

        self.assertLess(relative_error(py_result, jit_result), 0.0001/100)

    def test_ifelse(self):
        for _ in xrange(100):
            ARG = randint(1,10), randint(1,10)
            py_result = test_ifelse_py(*ARG)
            jit_result = test_ifelse(*ARG)

            self.assertEqual(py_result, jit_result)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

