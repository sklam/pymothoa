import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Int, Int])
def test_bool_and(A, B):
    if A > B and A < B*2:
        return 1
    return 0

@function(ret=Int, args=[Int, Int])
def test_bool_or(A, B):
    if A < B or A > B*2:
        return 1
    return 0

@function(ret=Bool, args=[Int, Int])
def test_bool_lte(A, B):
    return A <= B

@function(ret=Bool, args=[Float, Float])
def test_bool_gte(A, B):
    return A >= B

@function(ret=Bool, args=[Bool])
def test_bool_not(A):
    return not A

@function(ret=Bool, args=[Int])
def test_bool_not_int(A):
    return not A

@function(ret=Bool, args=[Float])
def test_bool_not_real(A):
    return not A

@function(ret=Bool, args=[Int])
def test_auto_convert_int(A):
    if A:
        return True
    else:
        return False

@function(ret=Bool, args=[Float])
def test_auto_convert_real(A):
    if A:
        return True
    else:
        return False

default_module.optimize()
#-------------------------------------------------------------------------------
import unittest
from random import random, randint

class Test(unittest.TestCase):

    def setUp(self):
        self.REP = 100

    def test_bool_and(self):
        for _ in xrange(self.REP):
            args = (randint(0, 100), randint(0, 100))
            self.assertEqual(test_bool_and(*args), test_bool_and.run_py(*args))

    def test_bool_or(self):
        for _ in xrange(self.REP):
            args = (randint(0, 100), randint(0, 100))
            self.assertEqual(test_bool_or(*args), test_bool_or.run_py(*args))

    def test_bool_lte(self):
        for _ in xrange(self.REP):
            args = (randint(0, 100), randint(0, 100))
            result = test_bool_lte(*args)
            self.assertEqual(result, (args[0]<=args[1]))

    def test_bool_gte(self):
        for _ in xrange(self.REP):
            args = (random(), random())
            result = test_bool_gte(*args)
            self.assertEqual(result, (args[0]>=args[1]))

    def test_bool_not(self):
        self.assertFalse(test_bool_not(True))
        self.assertTrue(test_bool_not(False))

    def test_bool_not_int(self):
        self.assertFalse(test_bool_not_int(1))
        self.assertTrue(test_bool_not_int(0))
        for _ in xrange(100):
            x = randint(-1000, 1000)
            self.assertEqual(not(x), test_bool_not_int(x))


    def test_bool_not_real(self):
        self.assertFalse(test_bool_not_real(1))
        self.assertTrue(test_bool_not_real(0))

        for _ in xrange(100):
            x = random()
            self.assertEqual(not(x), test_bool_not_real(x))

    def test_auto_convert_int(self):
        self.assertTrue(test_auto_convert_int(1))
        self.assertFalse(test_auto_convert_int(0))
        for _ in xrange(100):
            x = randint(-1000, 1000)
            self.assertEqual(bool(x), test_auto_convert_int(x))

    def test_auto_convert_real(self):
        self.assertTrue(test_auto_convert_real(1))
        self.assertFalse(test_auto_convert_real(0))
        for _ in xrange(100):
            x = random()
            self.assertEqual(bool(x), test_auto_convert_real(x))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

