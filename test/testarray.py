import logging
logging.basicConfig(level=logging.DEBUG)

from mamba.compiler import function
from mamba.types import *
from mamba.dialect import *

@function(ret=Float, args=[ [Float], Int])
def test_array(A, N):
    var ( temp = Double )
    temp = 0
    for i in xrange(N):
        temp = temp + A[i]
    return temp

from _util import benchmark, relative_error

def main():
    from random import random
    from numpy import array
    from ctypes import c_float

    print 'test_array'.center(80, '-')
    N = 1000
    A = array(map(lambda _: random()+1, range(N)), dtype=c_float)

    REP = 100

    with benchmark('Python', 'LLVM') as (timer_py, timer_jit):

        print 'Python'
        with timer_py:
            for _ in xrange(REP):
                py_result = test_array(A, N)
        print '\tResult =', py_result

        print 'LLVM'
        with timer_jit:
            for _ in xrange(REP):
                jit_result = test_array.jit(A, N)

        print '\tResult =',  jit_result
    assert relative_error(py_result, jit_result) < 0.01/100

    print
    print 'Assembly'.center(80, '=')
    print test_array.assembly()

if __name__ == '__main__':
    main()

