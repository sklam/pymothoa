
import logging
logging.basicConfig(level=logging.DEBUG)

from mamba.compiler import function
from mamba.types import *
from mamba.dialect import *

@function(ret=Int)
def test_constant():
    var (
        A = Int,
        B = Int,
        C = Int,
    )

    A = (123 + 321)*2
    B = 9
    C = A * B
    return C


@function(ret=Int, args=[Int])
def test_arg(B):
    var (
        A = Int,
        C = Int,
    )
    A = (123 - 321)*2
    C = A / B
    return C

@function(ret=Int, args=[Int])
def test_call(a):
    return test_arg(a)

@function(ret=Int64, args=[Int64])
def test_recur(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur(a-1)

def call(fn, *args):
    from time import time
    R = 500

    s = time()
    for i in xrange(R):
        ret_llvm = fn.jit(*args)
    e = time()
    print 'llvm: ', ret_llvm

    t_llvm = e-s


    s = time()
    for i in xrange(R):
        ret_python = fn(*args)
    e = time()
    print 'python:', ret_python

    t_python = e-s

    if not ret_llvm == ret_python:
        raise ValueError('Computation error!')

    if t_llvm < t_python:
        print 'LLVM is faster by %f seconds (%.1fx)'%(
            t_python-t_llvm,
            t_python/t_llvm,
            )
    elif t_python < t_llvm:
        print 'Python is faster by %f seconds (%.2fx)'%(
            t_llvm-t_python,
            1/(t_llvm/t_python),
            )

def main():

    print 'test_constant'.center(80, '-')
    call(test_constant)

    print 'test_arg'.center(80, '-')
    call(test_arg, 12)

    print 'test_call'.center(80, '-')
    call(test_call, 9)

    print 'test_recur'.center(80, '-')
    call(test_recur, 100)

if __name__ == '__main__':
    main()
