import logging; logging.basicConfig()

from pymothoa.jit import default_module, function      # include function decorator
from pymothoa.dialect import *
from pymothoa.types import *                # include all types

import numpy as np
from ctypes import c_float


@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_naive(Pn, Mn, Nn, n):
    var ( tmp = Float )

    for row in xrange(n):
        for col in xrange(n):
            tmp = 0
            for i in xrange(n):
                tmp += Mn[row*(n)+i]*Nn[i*(n)+col]
            Pn[row*(n)+col] = tmp

@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_cached(Pn, Mn, Nn, n):
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
    if n!=2: return
    var (dim=Int)
    dim=n*n
    for i in xrange(ct):
        matrixmul_cached(Pn[i*dim:], Mn[i*dim:], Nn[i*dim:], n)


@function(args=[Array(Float), Array(Float), Array(Float), Int])
def matrixmul_vector2x2(Pn, Mn, Nn, n):
    var (
          vecA = Vector(Float, 4),
          vecB = Vector(Float, 4),
          vecC = Vector(Float, 4),
        )
    if n!=2:
        return # only if n==2

    # Prepare vectors.

    for i in xrange(4): # A, B, C, D
        vecA[i] = Mn[i]

    vecB[0] = Nn[0] # P
    vecB[1] = Nn[2] # R
    vecB[2] = Nn[1] # Q
    vecB[3] = Nn[3] # S

    vecC[0] = Nn[1] # Q
    vecC[1] = Nn[3] # S
    vecC[2] = Nn[0] # P
    vecC[3] = Nn[2] # R

    vecB = vecA * vecB  # AP, BR, CQ, DS
    vecC = vecA * vecC  # AQ, BS, CP, DR

    var ( AP = Float, BR = Float, CQ = Float, DS = Float,
          AQ = Float, BS = Float, CP = Float, DR = Float, )

    AP = vecB[0]
    BR = vecB[1]
    CQ = vecB[2]
    DS = vecB[3]

    AQ = vecC[0]
    BS = vecC[1]
    CP = vecC[2]
    DR = vecC[3]

    Pn[0] = AP + BR
    Pn[1] = AQ + BS
    Pn[2] = CP + DR
    Pn[3] = CQ + DS

@function(args=[Array(Float), Array(Float), Array(Float), Int, Int])
def matrixmul_vector2x2_many(Pn, Mn, Nn, n, ct):
    if n!=2: return
    var (dim=Int)
    dim=n*n
    for i in xrange(ct):
        matrixmul_vector2x2(Pn[i*dim:], Mn[i*dim:], Nn[i*dim:], n)

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

    n = 2
    dim = n**2

    print 'n = %d' % n

    Mn = np.array(randomize_list(dim), dtype=c_float)
    Nn = np.array(randomize_list(dim), dtype=c_float)

    # calculate

    Golden = np.matrix(Mn.reshape((n,n))) * np.matrix(Nn.reshape((n,n)))

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_naive(Pn, Mn, Nn, n)
    verify(Golden, Pn, n)

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_cached(Pn, Mn, Nn, n)
    verify(Golden, Pn, n)

    Pn = np.zeros(dim, dtype=c_float)
    matrixmul_vector2x2(Pn, Mn, Nn, n)
    verify(Golden, Pn, n)

    with benchmark('Matrix-Matrix Multiply %dx%d'%(n,n)) as bm:
        REP = 10000

        Mn = np.array(randomize_list(dim*REP), dtype=c_float)
        Nn = np.array(randomize_list(dim*REP), dtype=c_float)

        Pn = np.zeros(dim*REP, dtype=c_float)
        Qn = np.zeros(dim*REP, dtype=c_float)

        Goldens = []
        with bm.entry(ENTRY_NUMPY):
            for i in xrange(REP):
                A = Mn[i*dim:(i+1)*dim]
                B = Nn[i*dim:(i+1)*dim]
                C = np.matrix(A.reshape((n,n))) * np.matrix(B.reshape((n,n)))
                Goldens.append(C)

#        with bm.entry(ENTRY_NAIVE):
#            for i in xrange(REP):
#                A = Mn[i*dim:(i+1)*dim]
#                B = Nn[i*dim:(i+1)*dim]
#                C = Pn[i*dim:(i+1)*dim]
#                matrixmul_naive(C, A, B, n)

#        with bm.entry(ENTRY_CACHED):
#            for i in xrange(REP):
#                A = Mn[i*dim:(i+1)*dim]
#                B = Nn[i*dim:(i+1)*dim]
#                C = Pn[i*dim:(i+1)*dim]
#                matrixmul_cached(C, A, B, n)

        with bm.entry(ENTRY_CACHED):
            matrixmul_cached_many(Pn, Mn, Nn, n, REP)

        with bm.entry(ENTRY_VECTOR):
            matrixmul_vector2x2_many(Qn, Mn, Nn, n, REP)

#        for i in xrange(REP):
#            P = Pn[i*dim:(i+1)*dim]
#            Q = Qn[i*dim:(i+1)*dim]
#            verify(Goldens[i], P, n)
#            verify(Goldens[i], Q, n)

    benchmark_summary()

if __name__ == '__main__':
    main()

