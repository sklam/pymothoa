# Introduction #

To leverage the power of Pymothoa, the function you are JIT-ing must perform enough computation. Otherwise, the overhead of JIT-ing can easily overshadow any benefit of the speedup of computation. Your JIT function will likely to use arrays for passing large datasets.

# Declaration #

Only unbounded arrays can be used as parameters. Here's an example of defining an unbound array of type **Float**:
```
from pymothoa.types import *

@function(args=[Array(Float)])
def foo(a_float_ary):
   ...
```

Since arrays are unbounded, the length of the array must also be passed along as parameter:

```
from pymothoa.types import *

@function(args=[Array(Float), Int])
def foo(a_float_ary, length):
   ...
```

You can create arrays of primitive types: **Int** (of any bits), **Float**, **Double**. But you cannot create arrays of aggregate types; such as, array of arrays or array of vectors.

# Automatic Conversion from Python Type #

When calling a JIT function that accepts an array as parameter, the caller can use list, tuple, native array (from array package) and Numpy array. In fact, any iterable type that implements the **`__len__`** method is supported.

To achieve the best performance, both Numpy array and the native array are recommended. **Just be careful that they must be declared with the same datatype as expected by the callee.**

To use the foo function from above, the caller should look like:
```
import numpy, ctypes
N = 10
A = numpy.array(range(N), dtype=ctypes.c_float) # explicitly declare the datatype.
foo(A, N)
```
Or,
```
import array
N = 10
A = array.array('f', range(N))
foo(A, N)
```

Other iterable types are converted by first creating a temporary copy. Therefore, the overhead is horrible.