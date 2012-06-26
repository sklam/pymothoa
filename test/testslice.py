import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Int, args=[Array(Int), Int, Int])
def test_slice(Ary, N, offset):
    var ( res = Int, Sliced = Slice(Int) )
    Sliced = Ary[offset:]

    res = 0
    for i in xrange(N-offset):
        res += Sliced[i]

    return res

default_module.optimize()
print test_slice.assembly()
#-------------------------------------------------------------------------------
import unittest
class Test(unittest.TestCase):
    def test_slice(self):
        from ctypes import c_int
        from numpy import array
        N = 100
        A = array(range(N), dtype=c_int)
        for offset in xrange(0, N):
            args = A, N, offset
            answer = test_slice(*args)
            logging.debug('args = %s | answer = %s', args, answer)
            self.assertEqual(answer, sum(range(N)[offset:]))

if __name__ == '__main__':
    unittest.main()
