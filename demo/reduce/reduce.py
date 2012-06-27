#!/usr/bin/env python

# Copyright (c) 2012, Siu Kwan Lam
# All rights reserved.

from pymothoa.jit import default_module, function
from pymothoa.types import *
from pymothoa.dialect import *

@function(ret=Float, args=[Array(Float), Int])
def reduction(A, n):
    var ( tmp = Float )
    tmp = 0
    for i in xrange(n):
        tmp += A[i]
    return tmp

@function(ret=Float, args=[Array(Float), Int])
def reduction_vector(A, n):
    if n/4*4!=n: return 0
    var ( tmp = Vector(Float, 4) )
    tmp = 0
    for i in xrange(0, n, 4):
        for j in xrange(4):
            tmp += A[i+j]

    var ( result = Float )
    result = 0
    for k in xrange(4):
        result = tmp[k]

    return result

#------------------------------------------------------------------------------

def main():
    from ctypes import c_float
    import numpy as np
    from array import array
    from random import random
    from pymothoa.util.testing import benchmark, benchmark_summary, relative_error

    N = 10000

    default_module.optimize()

    for t in xrange(4):
        data_list = map(lambda _: random(), xrange(N))
        data_array = array('f', data_list)
        data_numpy = np.array(data_list, dtype=c_float)

        golden = reduce(lambda X, Y: X+Y, data_list)
        answer = reduction(data_list, len(data_list))
        answer2 = reduction_vector(data_list, len(data_list))

        if relative_error(golden, answer)>0.01/100:
            raise AssertionError('Incorrect answer: reduction')
        if relative_error(golden, answer2)>0.01/100:
            raise AssertionError('Incorrect answer: reduction_vector')

        op = lambda X, Y: X+Y


        with benchmark('Reduction N=%d t=%d'%(N,t)) as bm:
            with bm.entry('Python list'):
                golden = reduce(op, data_list)

            with bm.entry('JIT list'):
                answer = reduction(data_list, N)

            with bm.entry('Python array'):
                golden = reduce(op, data_array)

            with bm.entry('JIT array'):
                answer = reduction(data_array, N)

            with bm.entry('Python numpy'):
                golden = np.add.reduce(data_numpy) # use numpy reduce function here

            with bm.entry('JIT numpy'):
                answer = reduction(data_numpy, N)

            with bm.entry('JIT vector array'):
                answer = reduction(data_array, N)

            with bm.entry('JIT vector numpy'):
                answer = reduction_vector(data_numpy, N)

    benchmark_summary()

if __name__ == '__main__':
    main()

