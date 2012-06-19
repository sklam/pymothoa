
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

@function(ret=Int, args=[Int, Int])
def test_forloop(val, repeat):
    for i in xrange(3, repeat):
        val = val + i
    return val

def main():
    from _util import test_and_compare

    print 'test_constant'.center(80, '-')
    test_and_compare(test_constant)

    print 'test_arg'.center(80, '-')
    test_and_compare(test_arg, 12)

    print 'test_test_and_compare'.center(80, '-')
    test_and_compare(test_call, 9)

    print 'test_recur'.center(80, '-')
    test_and_compare(test_recur, 100)

    print 'test_recur64'.center(80, '-')
    test_and_compare(test_recur64, 120)

    print 'test_float'.center(80, '-')
    test_and_compare(test_float, 321.321e+2)

    print 'test_double'.center(80, '-')
    test_and_compare(test_double, 321.321e+4)

    print 'test_forloop'.center(80, '-')
    test_and_compare(test_forloop, 1, 2**10)


if __name__ == '__main__':
    main()
