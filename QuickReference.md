# Enabling Pymothoa #

The Pymothoa dialect allows programmers to write C-like low-level code in the Python syntax. To enable the dialect in a function, add the **function** decorator.

For example:
```
from pymothoa.jit import function        # import function decorator
from pymothoa.types import *             # import datatypes

@function(ret=Int, args=[Float, Double]) # return integer and takes a float and a double as arguments.
def example1(a_float, a_double):
    ...
```

The **function** decorator takes 2 keyword arguments:
  * ret -- Declares the return type. Default to Void.
  * args -- Declares a list of arguments. Default to `[]`.


---


# Variables #

## Declaration ##
All variables must be declared with the **var** construct.

Example:
```
from pymothoa.jit import function        # import function decorator
from pymothoa.types import *             # import datatypes
from pymothoa.dialect import *           # import "var" construct

@function(...)
def example2():
    var ( an_int = Int, a_float = Float ) # declares an integer and a float variable
    ...
```

The **var** construct takes one or more declarations. A declaration is in the form of keyword argument in Python syntax. The _keyword_ declares the variable name. The _value_ declares the variable type.

## Types ##

  * signed integers -- Int, Int8, Int16, Int32, Int64
  * real -- Float, Double
  * others -- Array, Slice, Vector

Note: Length of **Int** is the same as length of **int** in C on the running system.

## Scope ##

There are no nested scope. A variable exists for the entire function.


---


# Constants #

Constant values can be immediate values or declared outside a Pymothoa function.

For example:
```
SIZE = 10

@function(...)
def foo(...):
    var ( a = Int )
    a += SIZE                   # SIZE is treated as a constant
    ...
```


---


# Strings #

Not supported yet!


---


# Arrays #

## Bounded Arrays ##

Internally allocated in the stack. Can only be used as variables.
Example:
```
var( my_array = Array(Int, 10) )    # allocates an array of 10 integers.
```

Note: The length of the array can also be a variable.

## Unbounded Arrays ##

It is internally a pointer. Can only be used as arguments.

Example:
```
@function(args=[Array(Int), Int])    # declares A as an unbounded array of integer, N as an integer.
def foo(A, N):
    ...
```

## Slice ##

Internally the same as an unbounded array. Can only be used as a variable.

Example:
```
var( my_array = Slice(Int) )    # allocates an unbounded array of integer.
```

To create a slice of an array (bounded or unbounded):
```
@function(args=[Array(Int), Int])
def foo(A, N):
    var (my_array = Slice(Int) )
    my_array = A                 # my_array is the same as A
    my_array = A[1:]             # my_array starts at the 2nd element of A
    my_array = A[5:]             # my_array starts at the 6th element of A
    foo(my_array, N-5)           # call foo recursively with a sliced array of A
```


---


# Vectors #

A portable vector type. LLVM can automatically convert vector types to scalar types with the target does not support vector instructions.

Vector can **not** be used in function argument. It can only be used as variables.

Example:
```
var( my_vec = Vector(Int, 4) )   # declares my_vec as a vector of 4 integers.
```

Note: The length of a vector **must be a constant**.


---


# Control Flow #

## If-Elif-Else ##

The **if-elif-else** construct behaves the same as in Python.

## For-Loop ##

Only accepts the **for ... in range(...)** pattern at this point. The **xrange** and **range** builtins are the same in Pymothoa. They do not generate a list nor a generator.

In fact, **for i in range(Begin, End, Step)** is equal to the following in C:
```
for ( int i=Begin; i<End; i+=Step ){
    ...
}
```

The counter variable is automatically declared as an integer.

Note: the **for ... else** construct is not supported.

## While-Loop ##

The **while** construct behaves the same as in Python.

Note: the **while ... else** construct is not supported.


---


# Exceptions #

There are no exceptions.


---


# Type Casting #

Types are casted automatically. No explicit type casting yet.


---


# Optimization #

By default, all functions are compiled into the 'default' module.

To access the 'default' module:
```
from pymothoa.jit import default_module
```

Call optimize() on a module to run the optimization passes.

Example:
```
default_module.optimize()   # Optimize the 'default' module
```