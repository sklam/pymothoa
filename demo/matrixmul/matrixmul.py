import logging; logging.basicConfig()

from pymothoa.jit import default_module, function      # include function decorator
from pymothoa.dialect import *
from pymothoa.types import *                # include all types

import numpy as np
from ctypes import c_float

@function(args=[Array(Float), Array(Float), Array(Float), Int, Int])
def matrixmul_naive(Pn, Mn, Nn, n, stride):
    var ( tmp = Float, RL = Int )
    RL = n + stride
    for row in xrange(n):
        for col in xrange(n):
            tmp = 0
            for i in xrange(n):
                tmp += Mn[row*RL+i]*Nn[i*RL+col]
            Pn[row*RL+col] = tmp

@function(args=[Array(Float), Array(Float), Array(Float), Int, Int])
def matrixmul_cached(Pn, Mn, Nn, n, stride):
    var (
          NnCache = Array(Float, n),
          total   = Float,
          RL = Int,
        )
    RL = n + stride
    for col in xrange(n):
        # Cache a column in Nn, and hold it for all rows of Mn.
        for i in xrange(n):
            NnCache[i] = Nn[i*RL+col]

        for row in xrange(n):
            # Calculate product of an element
            total = 0
            for k in xrange(n):
                total += Mn[row*RL+k]*NnCache[k]

            # Store elements
            Pn[row*RL+col] = total

@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_blocked(Pn, Mn, Nn, n):
    if n <= 1024:
        matrixmul_cached(Pn, Mn, Nn, n, 0)
        return

    for j in xrange(n/2):
        for i in xrange(n/2):
            pass

@function(args=[Array(Float), Array(Float), Array(Float)])
def matrixmul_strassen_2x2(Pn, Mn, Nn):
    # Strassen algorithm
    var ( A = Array(Float, 7), )
    A[0] = (Mn[0]+Mn[3])*(Nn[0]+Nn[3])
    A[1] = (Mn[2]+Mn[3])*Nn[0]
    A[2] = Mn[0]*(Nn[1]-Nn[3])
    A[3] = Mn[3]*(Nn[2]-Nn[0])
    A[4] = (Mn[0]+Mn[1])*Nn[3]
    A[5] = (Mn[2]-Mn[0])*(Nn[0]+Nn[1])
    A[6] = (Mn[1]-Mn[3])*(Nn[2]+Nn[3])

    Pn[0] = A[0]+A[3]-A[4]+A[6]
    Pn[1] = A[2]+A[4]
    Pn[2] = A[1]+A[3]
    Pn[3] = A[0]-A[1]+A[2]+A[5]

default_module.optimize()
#-------------------------------------------------------------------------------

from pymothoa.util.testing import benchmark, benchmark_summary, relative_error

def randomize_list(length):
    from random import random
    return [random() for _ in xrange(length)]

def verify(Golden, Pn, n):
    Pn = np.matrix(Pn.reshape((n,n)))
    for y in xrange(n):
        for x in xrange(n):
            prod = Pn[y, x]
            gold = Golden[y, x]
            if relative_error(gold, prod) > 0.01/100 :
                raise AssertionError('Incorrect result')

def main():
    print 'Matrix-Matrix Multiplication Demo'.center(80, '=')

    n = 1024
    dim = n**2

    Mn = np.array(randomize_list(dim), dtype=c_float)
    Nn = np.array(randomize_list(dim), dtype=c_float)

    print 'Mn =', Mn.reshape((n,n))
    print 'Nn =', Nn.reshape((n,n))

    # calculate

    Golden = np.matrix(Mn.reshape((n,n))) * np.matrix(Nn.reshape((n,n)))

#    Pn = np.zeros(dim, dtype=c_float)
#    matrixmul_naive(Pn, Mn, Nn, n, 0)
#    verify(Golden, Pn, n)

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_cached(Pn, Mn, Nn, n, 0)
    verify(Golden, Pn, n)

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_blocked(Pn, Mn, Nn, n)
    verify(Golden, Pn, n)

    data = []
    with benchmark('Matrix-Matrix Multiply') as bm:

        with bm.entry('Numpy'):
            Golden = np.matrix(Mn.reshape((n,n))) * np.matrix(Nn.reshape((n,n)))

#        Pn = np.zeros(dim, dtype=c_float)
#        with bm.entry('JIT Naive'):
#            matrixmul_naive(Pn, Mn, Nn, n)
#        verify(Golden, Pn, n)

        with bm.entry('JIT Cached'):
            matrixmul_cached(Pn, Mn, Nn, n, 0)
        with bm.entry('JIT Blocked'):
            matrixmul_blocked(Pn, Mn, Nn, n)

    # report benchmark
    benchmark_summary()


if __name__ == '__main__':
#    import cProfile
#    cProfile.run('main()', 'profile.dat')
    main()
