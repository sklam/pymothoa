
import logging
#logging.basicConfig(level=logging.DEBUG)

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

@function(ret=Int, args=[Int])
def test_recur(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur(a-1)


@function(ret=Int64, args=[Int64])
def test_recur64(a):
    if a <= 1:
        return 1
    else:
        return a + test_recur64(a-1)
                

@function(ret=Float, args=[Float])
def test_float(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_float(a/1.1)

@function(ret=Double, args=[Double])
def test_double(a):
    if a <= 1:
        return 1.0
    else:
        return a + test_double(a/1.1)

def call(fn, *args):
    from time import time
    R = 100

    ret_llvm = fn.jit(*args)
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

    relative_error = float(abs(ret_llvm-ret_python))/ret_python
    
    if relative_error > 1e-5:
        print 'relative_error =', relative_error
        raise ValueError('Computation error!')

    if t_llvm < t_python:
        print 'LLVM is faster by %f seconds (%.1fx)'%(
            t_python-t_llvm,
            t_python/t_llvm,
            )
    elif t_python < t_llvm:
        print 'Python is faster by %f seconds (%.2fx)'%(
            t_llvm-t_python,
            -t_llvm/t_python,
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

    print 'test_recur64'.center(80, '-')
    call(test_recur64, 120)

    print 'test_float'.center(80, '-')
    call(test_float, 321.321e+2)
    
    print 'test_double'.center(80, '-')
    call(test_double, 321.321e+4)

if __name__ == '__main__':
    main()
