# Copyright (c) 2012, Siu Kwan Lam
# All rights reserved.
#
# Matrix-Matrix Multiplication Demo (Square matrices only)
#
# This demo implements a simple matrix-matrix multiplication and compares
# against the Numpy implementation. You will need Numpy to run this demo.
#
# Run to see benchmark against Numpy.
#
import logging; logging.basicConfig(level=logging.DEBUG)

# Import JIT features
from pymothoa.jit import default_module, function

# Import constructs for the Pymothoa dialect
from pymothoa.dialect import *

# Import the Pymothoa types
from pymothoa.types import *                # include all types

# Import Numpy and ctypes
import numpy as np
from ctypes import c_float

@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_naive(Pn, Mn, Nn, n):
    '''Implements a naive implementation of matrix-matrix multiplication.

    All arguments must be typed. They are declared as "args" in the function
    decorator.

    Pn, Mn, Nn -- arrays of float
    n -- integer indicating the length of the arrays
    '''
    # Declare variables
    var ( tmp = Float )

    # Loop variables are declared automatically.
    # 'xrange' and 'range' now has the same meaning but they are different
    # from the raw Python code. Here, it means,
    # for ( int row=0; row<n; row++ )
    for row in xrange(n):
        for col in xrange(n):
            tmp = 0
            for i in xrange(n):
                # Subscript works, but no bound checking.
                tmp += Mn[row*(n)+i]*Nn[i*(n)+col]
            Pn[row*(n)+col] = tmp

@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_cached(Pn, Mn, Nn, n):
    '''Another implementation that is more efficient in the memory access.
    '''
    var (
          NnCache = Array(Float, n),
          total   = Float,
        )

    for col in xrange(n):
        # Cache a column in Nn, and hold it for all rows of Mn.
        for i in xrange(n):
            NnCache[i] = Nn[i*(n)+col]

        for row in xrange(n):
            # Calculate product of an element
            total = 0
            for k in xrange(n):
                total += Mn[row*(n)+k]*NnCache[k]

            # Store elements
            Pn[row*(n)+col] = total

@function(args=[Array(Float), Array(Float), Array(Float), Int, Int])
def matrixmul_cached_many(Pn, Mn, Nn, n, ct):
    '''Iterate over matrixmul_cached() multiple times to be more efficient.
    Otherwise, the speed will not match Numpy at all.
    There are some overheads for each call.
    '''
    var (dim=Int)
    dim = n*n
    for i in xrange(ct):
        matrixmul_cached(Pn[i*dim:], Mn[i*dim:], Nn[i*dim:], n)


# We have done building the JIT code. Optimize it for speed.
default_module.optimize()

#-------------------------------------------------------------------------------

from pymothoa.util.testing import benchmark, benchmark_summary, relative_error

def randomize_list(length):
    '''Create randomized list of float for testing.
    '''
    from random import random
    return [random() for _ in xrange(length)]

def verify(Golden, Pn, n):
    '''Verify the content of Pn against Golden.
    '''
    Pn = np.matrix(Pn.reshape((n,n)))
    for y in xrange(n):
        for x in xrange(n):
            prod = Pn[y, x]
            gold = Golden[y, x]
            relerr = relative_error(gold, prod)
            # print 'relerr =', relerr, prod, gold
            if relerr > 0.01/100 :
                raise AssertionError('Incorrect result')

def main():
    print 'Matrix-Matrix Multiplication Demo'.center(80, '=')

    ENTRY_NUMPY = 'numpy'
    ENTRY_CACHED = 'cached-jit'
    ENTRY_NAIVE = 'naive-jit'
    ENTRY_VECTOR = 'vector-jit'

    # Set the number of element per row (or column) of matrix.
    # Feel free to change the value.
    n = 8

    # Total number of elements in the matrices. n^2
    dim = n**2

    print 'n = %d' % n

    # Generate randomized matrices
    Mn = np.array(randomize_list(dim), dtype=c_float)
    Nn = np.array(randomize_list(dim), dtype=c_float)

    # Calculate golden values using Numpy
    Golden = np.matrix(Mn.reshape((n,n))) * np.matrix(Nn.reshape((n,n)))

    ## Disable naive implementation
    #
    #    Pn = np.zeros(dim, dtype=c_float)
    #    matrixmul_naive(Pn, Mn, Nn, n)
    #    verify(Golden, Pn, n)

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_cached(Pn, Mn, Nn, n)
    verify(Golden, Pn, n)

    with benchmark('Matrix-Matrix Multiply %dx%d'%(n,n)) as bm:
        # Number of iteration
        REP = 1000

        # Randomize input
        Mn = np.array(randomize_list(dim*REP), dtype=c_float)
        Nn = np.array(randomize_list(dim*REP), dtype=c_float)

        # Create storage for product matrix
        Pn = np.zeros(dim*REP, dtype=c_float)

        Goldens = []
        with bm.entry(ENTRY_NUMPY):
            for i in xrange(REP):
                A = Mn[i*dim:(i+1)*dim]
                B = Nn[i*dim:(i+1)*dim]
                C = np.matrix(A.reshape((n,n))) * np.matrix(B.reshape((n,n)))
                Goldens.append(C)

        with bm.entry(ENTRY_CACHED):
            matrixmul_cached_many(Pn, Mn, Nn, n, REP)

        for i in xrange(REP): # Verify again.
            P = Pn[i*dim:(i+1)*dim]
            verify(Goldens[i], P, n)

    benchmark_summary()

if __name__ == '__main__':
    main()

