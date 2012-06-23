import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function, declaration
from pymothoa.types import *
from pymothoa.dialect import *

@declaration(ret=Int, args=[Int])
def test_callee(A): pass

@function(ret=Int, args=[Int])
def test_caller(A):
    return test_callee(A)*3

@function(ret=Int, args=[Int])
def test_callee(A):
    return A*2

import unittest
class Test(unittest.TestCase):
    def test_callee(self):
        answer = test_callee(2)
        self.assertTrue(answer==2*2)
        answer = test_callee(123)
        self.assertTrue(answer==123*2)

    def test_caller(self):
        answer = test_caller(2)
        self.assertTrue(answer==2*2*3)
        answer = test_caller(123)
        self.assertTrue(answer==123*2*3)

if __name__ == '__main__':
    unittest.main()
