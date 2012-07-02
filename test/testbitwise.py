import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Int, Int])
def test_bitwise_and(A, B):
    return A & B

@function(ret=Int, args=[Int, Int])
def test_bitwise_or(A, B):
    return A | B

@function(ret=Int, args=[Int, Int])
def test_lshift(A, n):
    return A << n

@function(ret=Int, args=[Int, Int])
def test_rshift(A, n):
    return A >> n # arithmetic shift

default_module.optimize()
#-------------------------------------------------------------------------------
import unittest
from random import random, randint

class Test(unittest.TestCase):

    def setUp(self):
        self.REP = 100

    def test_bitwise_and(self):
        for _ in xrange(self.REP):
            args = (randint(0, 100), randint(0, 100))
            self.assertEqual(test_bitwise_and(*args), test_bitwise_and.run_py(*args))

    def test_bitwise_or(self):
        for _ in xrange(self.REP):
            args = (randint(0, 100), randint(0, 100))
            self.assertEqual(test_bitwise_or(*args), test_bitwise_or.run_py(*args))

    def test_lshift(self):
        for amt in xrange(31):
            args = (1, amt)
            self.assertEqual(test_lshift(*args), test_lshift.run_py(*args))

        for _ in xrange(self.REP):
            args = (randint(-0xfff, 0xfff), randint(0, 16))
            self.assertEqual(test_lshift(*args), test_lshift.run_py(*args))

    def test_rshift(self):

        for amt in xrange(31):
            args = (-1, amt)
            self.assertEqual(test_rshift(*args), test_rshift.run_py(*args))

        for _ in xrange(self.REP):
            args = (randint(-0xfff, 0xfff), randint(0, 31))
            self.assertEqual(test_rshift(*args), test_rshift.run_py(*args))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

