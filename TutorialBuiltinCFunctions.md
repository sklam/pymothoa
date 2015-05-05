# Introduction #

Since Pymothoa is intended for compute-intensive code, it will not be useful without access to the math functions in the C library. This tutorial explains how to use the math functions and other C-library functions.

# math.h #

To use the functions in math.h, import the **pymothoa.builtins.math** module and the **pymothoa.jit.declare\_builtin** function.

For example, to use the sinf() function:
```
from pymothoa.jit import declare_builtin
from pymothoa.builtins import math

fn_sinf = declare_builtin(*math.sinf) # do not forget the *
```

This declares the sinf() function in the default JIT module. Now, you can call _fn\_sinf_ inside your JIT function, or use it directly in your Python code (however, it will be slower).

All math functions in the **pymothoa.builtins.math** module have the same prototype as the corresponding C functions.

Here's a list of all the implemented double-precision math functions:
  * trigonometric -- sin, cos, tan, asin, acos, atan, sinh, cosh, tanh;
  * power -- sqrt, pow;
  * exponential -- exp, log, log10;
  * misc -- fabs, ceil, floor, fmod;

To use the single-precision version, append 'f' to the function name.

# stdio.h #
_TODO..._