# Introduction #

This is a quick introduction to Pymothoa so that you can start JIT compiling your Python code into native code in a few minutes. The following instruction is intended for `*`nix users.

# What is Pymothoa? #

I do a lot of prototyping and experimenting using Python. I wanted a way to get performance quickly, without re-writing my algorithms in C for a C-extension. To solve the problem, I came up with Pymothoa.

Pymothoa is a JIT extension to the Python language. It uses LLVM for the JIT ability. Pymothoa is compatible with CPython 2.6+ and LLVM 3.1 (other version may also work but I have not tested yet.)

# Installation #

First, you need a copy of LLVM from http://llvm.org. Compile it with:
```
$ ./configure --enable-optimized
$ make all
```

Checkout out a copy of the Pymothoa source tree. Make sure you have "llvm-config" in your PATH environment variable. Your "llvm-config" is in the "`<`llvm-root-dir`>`/Release+Asserts/bin".

Compile and install the extension with:
```
$ python setup.py build
$ python setup.py install --user
```

(Note: The above command uses the per-user install. Omit "--user" to use system-wide install.)

Optionally, you can run the test suite in the _test_ directory of the Pymothoa source tree to make sure everything is working. Simply run "make all" in the test directory. If the test ends with "OK", the installation is successful.

## Hello World ##

Let's make a hello world application. Instead of printing "Hello World", our first program will compute the reduce-sum of an array of integers.

Create a new Python script "hello.py" with the following contents:
```
def reduce_sum(A, n):
    total = 0
    for i in xrange(n):
        total += A[i]
    return total

def main():
    N = 10
    print reduce_sum(range(N), N)

if __name__ == '__main__':
    main()
```

At this point, the file contains pure Python code. No JIT yet. Try to run it and make sure you see 45 printed on the terminal.

To enable JIT, add the following lines to the start of the file:
```
from pymothoa.jit import function
from pymothoa.dialect import *
from pymothoa.types import *

@function(ret=Int, args=[Array(Int), Int])
def reduce_sum(A, n):
...
```

The **function** decorator marks the reduce\_sum() function for JIT and declares the return type to be an integer, the arguments to be an array of integer and an integer.

Run the script and ... ERROR!
```
When compiling function "__main__.reduce_sum (in hello.py:7:5)":
def reduce_sum(A, n):
    total = 0
----^
    for i in xrange(n):

Symbol has not been defined.
Hint: All variables must be defined using var ( Name = Type, ... ) construct prior to use.
```

The error message says that the variable _total_ is not declared. In Pymothoa, all variables must be declared and typed.

Modify the code to look like:
```
...
@function(args=[Array(Int), Int])
def reduce_sum(A, n):
    var ( total = Int ) # add declaration of total
    total = 0
    ...
```

We are not declaring _i_ because the **for** _variable_ **in xrange(...)** construct will automatically declare _i_ as an integer. (**range** and **xrange** are the same in Pymothoa.)

Try to run the script again. It should work this time. But, how do you know it is JIT compiling? Probably, seeing the assembly is more convincing.

Modify the code:
```
def main():
    N = 10
    print reduce_sum(range(N), N)
    print reduce_sum.assembly()    # add this line to print the assembly code
```

Your "hello.py" file should looks like the following at this point:
```
from pymothoa.jit import function
from pymothoa.dialect import *
from pymothoa.types import *

@function(ret=Int, args=[Array(Int), Int])
def reduce_sum(A, n):
    var ( total = Int )
    total = 0
    for i in xrange(n):
        total += A[i]
    return total

def main():
    N = 10
    print reduce_sum(range(N), N)
    print reduce_sum.assembly()

if __name__ == '__main__':
    main()
```

Now, you can see assembly code printed in the terminal. If you are still not convinced, try to time the execution time.

## What to do next? ##

Try experimenting and take a look at the demo and test suite in the _demo_ and _test_ directory, respectively. There will be more tutorials soon.