import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function, declare_builtin
from pymothoa.builtins import math as cmath
from pymothoa.types import *
from pymothoa.dialect import *


sinf = declare_builtin(*cmath.sinf)
sin = declare_builtin(*cmath.sin)

cosf = declare_builtin(*cmath.cosf)
cos = declare_builtin(*cmath.cos)

tanf = declare_builtin(*cmath.tanf)
tan = declare_builtin(*cmath.tan)

asinf = declare_builtin(*cmath.asinf)
asin = declare_builtin(*cmath.asin)

acosf = declare_builtin(*cmath.acosf)
acos = declare_builtin(*cmath.acos)

atanf = declare_builtin(*cmath.atanf)
atan = declare_builtin(*cmath.atan)


sinhf = declare_builtin(*cmath.sinhf)
sinh = declare_builtin(*cmath.sinh)

coshf = declare_builtin(*cmath.coshf)
cosh = declare_builtin(*cmath.cosh)

tanhf = declare_builtin(*cmath.tanhf)
tanh = declare_builtin(*cmath.tanh)


sqrtf = declare_builtin(*cmath.sqrtf)
sqrt = declare_builtin(*cmath.sqrt)

powf = declare_builtin(*cmath.powf)
pow = declare_builtin(*cmath.pow)

expf = declare_builtin(*cmath.expf)
exp = declare_builtin(*cmath.exp)

logf = declare_builtin(*cmath.logf)
log = declare_builtin(*cmath.log)

log10f = declare_builtin(*cmath.log10f)
log10 = declare_builtin(*cmath.log10)

fabsf = declare_builtin(*cmath.fabsf)
fabs = declare_builtin(*cmath.fabs)

ceilf = declare_builtin(*cmath.ceilf)
ceil = declare_builtin(*cmath.ceil)

floorf = declare_builtin(*cmath.floorf)
floor = declare_builtin(*cmath.floor)

fmodf = declare_builtin(*cmath.fmodf)
fmod = declare_builtin(*cmath.fmod)

# Tri

@function(ret=Float, args=[Float])
def test_sinf(radian):
    return sinf(radian)

@function(ret=Double, args=[Double])
def test_sin(radian):
    return sin(radian)

@function(ret=Float, args=[Float])
def test_cosf(radian):
    return cosf(radian)

@function(ret=Double, args=[Double])
def test_cos(radian):
    return cos(radian)

@function(ret=Float, args=[Float])
def test_tanf(radian):
    return tanf(radian)

@function(ret=Double, args=[Double])
def test_tan(radian):
    return tan(radian)

# Arc-Tri

@function(ret=Float, args=[Float])
def test_asinf(val):
    return asinf(val)

@function(ret=Double, args=[Double])
def test_asin(val):
    return asin(val)

@function(ret=Float, args=[Float])
def test_acosf(val):
    return acosf(val)

@function(ret=Double, args=[Double])
def test_acos(val):
    return acos(val)

@function(ret=Float, args=[Float])
def test_atanf(val):
    return atanf(val)

@function(ret=Double, args=[Double])
def test_atan(val):
    return atan(val)

# Hyperbolic

@function(ret=Float, args=[Float])
def test_sinhf(val):
    return sinhf(val)

@function(ret=Double, args=[Double])
def test_sinh(val):
    return sinh(val)

@function(ret=Float, args=[Float])
def test_coshf(val):
    return coshf(val)

@function(ret=Double, args=[Double])
def test_cosh(val):
    return cosh(val)

@function(ret=Float, args=[Float])
def test_tanhf(val):
    return tanhf(val)

@function(ret=Double, args=[Double])
def test_tanh(val):
    return tanh(val)

# Power

@function(ret=Float, args=[Float])
def test_sqrtf(val):
    return sqrtf(val)

@function(ret=Double, args=[Double])
def test_sqrt(val):
    return sqrt(val)

@function(ret=Float, args=[Float, Float])
def test_powf(val, exp):
    return powf(val, exp)

@function(ret=Double, args=[Double, Double])
def test_pow(val, exp):
    return pow(val, exp)

# exponential

@function(ret=Float, args=[Float])
def test_expf(val):
    return expf(val)

@function(ret=Double, args=[Double])
def test_exp(val):
    return exp(val)

@function(ret=Float, args=[Float])
def test_logf(val):
    return logf(val)

@function(ret=Double, args=[Double])
def test_log(val):
    return log(val)

@function(ret=Float, args=[Float])
def test_log10f(val):
    return log10f(val)

@function(ret=Double, args=[Double])
def test_log10(val):
    return log10(val)

# misc
@function(ret=Float, args=[Float])
def test_fabsf(val):
    return fabsf(val)

@function(ret=Double, args=[Double])
def test_fabs(val):
    return fabs(val)

@function(ret=Float, args=[Float])
def test_ceilf(val):
    return ceilf(val)

@function(ret=Double, args=[Double])
def test_ceil(val):
    return ceil(val)

@function(ret=Float, args=[Float])
def test_floorf(val):
    return floorf(val)

@function(ret=Double, args=[Double])
def test_floor(val):
    return floor(val)

@function(ret=Float, args=[Float, Float])
def test_fmodf(n, d):
    return fmodf(n, d)

@function(ret=Double, args=[Double, Double])
def test_fmod(n, d):
    return fmod(n, d)

# combined experiment
@function(ret=Double, args=[Double, Double])
def test_pythagoras(x, y):
    return sqrt(x*x + y*y)

default_module.optimize()

#-------------------------------------------------------------------------------

import unittest
from pymothoa.util.testing import relative_error, benchmark, benchmark_summary

def random(lo=-1, hi=1):
    from random import uniform
    return uniform(lo, hi)

class Test(unittest.TestCase):
    def test_sin(self):
        from math import sin
        for _ in xrange(100):
            radian = random()

            golden = sin(radian)

            answer = test_sinf(radian)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_sin(radian)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_cos(self):
        from math import cos
        for _ in xrange(100):
            radian = random()

            golden = cos(radian)

            answer = test_cosf(radian)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_cos(radian)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_tan(self):
        from math import tan
        for _ in xrange(100):
            radian = random()

            golden = tan(radian)

            answer = test_tanf(radian)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_tan(radian)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_asin(self):
        from math import asin
        for _ in xrange(100):
            val = random()

            golden = asin(val)

            answer = test_asinf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_asin(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_acos(self):
        from math import acos
        for _ in xrange(100):
            val = random()

            golden = acos(val)

            answer = test_acosf(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

            answer = test_acos(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_atan(self):
        from math import atan
        for _ in xrange(100):
            val = random()

            golden = atan(val)

            answer = test_atanf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_atan(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_sinh(self):
        from math import sinh
        for _ in xrange(100):
            val = random()

            golden = sinh(val)

            answer = test_sinhf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_sinh(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_cosh(self):
        from math import cosh
        for _ in xrange(100):
            val = random()

            golden = cosh(val)

            answer = test_coshf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_cosh(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_tanh(self):
        from math import tanh
        for _ in xrange(100):
            val = random()

            golden = tanh(val)

            answer = test_tanhf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_tanh(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_sqrt(self):
        from math import sqrt
        for _ in xrange(100):
            val = random(0, 10)

            golden = sqrt(val)

            answer = test_sqrtf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_sqrt(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_pow(self):
        from math import pow
        for _ in xrange(100):
            val = random(0, 10)
            exp = random()

            golden = pow(val, exp)

            answer = test_powf(val, exp)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_pow(val, exp)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_exp(self):
        from math import exp
        for _ in xrange(100):
            val = random()
            golden = exp(val)

            answer = test_expf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_exp(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_log(self):
        from math import log
        for _ in xrange(100):
            val = random(1, 1e10)
            golden = log(val)

            answer = test_logf(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_log(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_log10(self):
        from math import log10
        for _ in xrange(100):
            val = random(1, 1e10)

            golden = log10(val)

            answer = test_log10f(val)
            self.assertLess(relative_error(golden, answer), 0.01/100)

            answer = test_log10(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_fabs(self):
        for _ in xrange(100):
            val = random()
            golden = abs(val)

            answer = test_fabsf(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

            answer = test_fabs(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_ceil(self):
        from math import ceil
        for _ in xrange(100):
            val = random(lo=-100, hi=100)
            golden = ceil(val)

            answer = test_ceilf(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

            answer = test_ceil(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_floor(self):
        from math import floor
        for _ in xrange(100):
            val = random(lo=-100, hi=100)
            golden = floor(val)

            answer = test_floorf(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

            answer = test_floor(val)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_fmod(self):
        from math import fmod
        for _ in xrange(100):
            numerator = random(-100, 100)
            denominator = random(-10, 10)

            golden = fmod(numerator, denominator)

            answer = test_fmodf(numerator, denominator)
            self.assertLess(relative_error(golden, answer), 0.5/100)

            answer = test_fmod(numerator, denominator)
            self.assertLess(relative_error(golden, answer), 0.001/100)

    def test_pythagoras(self):
        from math import sqrt
        def pythagoras(x, y):
            return sqrt(x*x + y*y)

        for _ in xrange(100):
            x = random()
            y = random()
            golden = pythagoras(x, y)
            answer = test_pythagoras(x, y)

            self.assertLess(relative_error(golden, answer), 0.001/100)

        with benchmark('Pythagoras') as bm:
            REP = 10000

            with bm.entry('Python'):
                for _ in xrange(REP):
                    x = random()
                    y = random()
                    z = pythagoras(x, y)


            with bm.entry('JIT'):
                for _ in xrange(REP):
                    x = random()
                    y = random()
                    z = test_pythagoras(x, y)

            with bm.entry('JIT-direct'):
                # Interestingly, Python function call is very slow.
                # Calling the C-function directly gives a great speedup.
                for _ in xrange(REP):
                    x = random()
                    y = random()
                    z = test_pythagoras.c_funcptr(x, y)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    unittest.TextTestRunner(verbosity=2).run(suite)

    benchmark_summary()

