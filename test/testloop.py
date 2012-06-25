import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Int, Int])
def test_loop_3arg(A, S):
    var ( res = Int )
    for i in xrange(0, A, S):
        res += i
    return res

import unittest
class Test(unittest.TestCase):
    def test_callee(self):
        N = 100
        for i in xrange(1, N):
            args = N, i
            print args
            answer = test_loop_3arg(*args)
            print answer
            self.assertEqual(answer, sum(xrange(0, *args)))

if __name__ == '__main__':
    unittest.main()
