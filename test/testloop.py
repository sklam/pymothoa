import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Int, Int])
def test_loop(A, S):
    var ( res = Int )
    for i in xrange(0, A, S):
        res += i
    return res

default_module.optimize()
#-------------------------------------------------------------------------------
import unittest
class Test(unittest.TestCase):
    def test_loop(self):
        N = 100
        for i in xrange(1, N):
            args = N, i
            answer = test_loop(*args)
            logging.debug('args = %s | answer = %s', args, answer)
            self.assertEqual(answer, sum(xrange(0, *args)))

if __name__ == '__main__':
    unittest.main()
