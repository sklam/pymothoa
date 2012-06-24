import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
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


import unittest
from random import random, randint

class Test(unittest.TestCase):

    def test_bool_and(self):
        args = (1, 2)
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))
        args = (2, 2)
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))
        args = (3, 2)
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))
        args = (4, 2)
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))
        args = (5, 2)
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))
        args = (randint(0, 100), randint(0, 100))
        self.assertTrue(test_bool_and(*args)==test_bool_and.run_py(*args))

    def test_bool_or(self):
        args = (1, 2)
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))
        args = (2, 2)
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))
        args = (3, 2)
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))
        args = (4, 2)
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))
        args = (5, 2)
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))
        args = (randint(0, 100), randint(0, 100))
        self.assertTrue(test_bool_or(*args)==test_bool_or.run_py(*args))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

