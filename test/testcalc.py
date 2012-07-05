
import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *


@function(ret=Int, args=[Int, Int])
def test_power_int(X, Y):
    return X ** Y

@function(ret=Float, args=[Float, Float])
def test_power_float(X, Y):
    return X ** Y

@function(ret=Int, args=[Int, Int])
def test_mod_int(X, Y):
    return X % Y

@function(ret=Float, args=[Float, Float])
def test_mod_float(X, Y):
    return X % Y


default_module.optimize()

# -------------------------------------------------------------------

import unittest
from random import random, randint
from numpy import array
from ctypes import c_float
from pymothoa.util.testing import relative_error

class Test(unittest.TestCase):

    def test_power_int(self):
        for _ in xrange(100):
            ARG = randint(0,10), randint(0,8)
            py_result = test_power_int.run_py(*ARG)
            jit_result = test_power_int(*ARG)
            error = relative_error(py_result, jit_result)
            self.assertLess(error, 0.01/100)

    def test_power_float(self):
        for _ in xrange(100):
            ARG = random(), random()
            py_result = test_power_float.run_py(*ARG)
            jit_result = test_power_float(*ARG)
            error = relative_error(py_result, jit_result)
            self.assertLess(error, 0.01/100)


    def test_mod_int(self):
        for _ in xrange(100):
            ARG = randint(0,10), randint(1,8)
            py_result = test_mod_int.run_py(*ARG)
            jit_result = test_mod_int(*ARG)
            error = relative_error(py_result, jit_result)
            self.assertLess(error, 0.01/100)

    def test_mod_float(self):
        for _ in xrange(100):
            ARG = random(), random()
            py_result = test_mod_float.run_py(*ARG)
            jit_result = test_mod_float(*ARG)
            error = relative_error(py_result, jit_result)
            self.assertLess(error, 0.05/100)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

