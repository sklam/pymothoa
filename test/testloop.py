import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Int, Int])
def test_forloop(A, S):
    var ( res = Int )
    for i in xrange(0, A, S):
        res += i
    return res

@function(ret=Int, args=[Int, Int])
def test_whileloop(A, S):
    var ( i = Int, res = Int )
    i = 0
    while i<A:
        res += i
        i+=S
    return res


default_module.optimize()
#-------------------------------------------------------------------------------
import unittest
class Test(unittest.TestCase):
    def test_forloop(self):
        N = 100
        for i in xrange(1, N):
            args = N, i
            answer = test_forloop(*args)
            logging.debug('args = %s | answer = %s', args, answer)
            self.assertEqual(answer, sum(xrange(0, *args)))

    def test_whileloop(self):
        N = 100
        for i in xrange(1, N):
            args = N, i
            answer = test_forloop(*args)
            logging.debug('args = %s | answer = %s', args, answer)
            self.assertEqual(answer, sum(xrange(0, *args)))

if __name__ == '__main__':
    unittest.main()
