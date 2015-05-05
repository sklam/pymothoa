**Important Notice**

Pymothoa has been inactive because I have joined forces with the Numba team.  Some ideas in Pymothoa are merging into Numba's AST branch. Numba currently provides a translation path from bytecode, and a translation path from AST.  See https://github.com/numba/numba.



---


Pymothoa extends the Python language by adding JIT compilation without any modification of the interpreter source code. Pymothoa lives at the application level. It uses the AST generated by Python. Therefore, users write in the original Python syntax but with a new contextual meaning in some cases using the new dialect provided by Pymothoa.

User uses the decorators provided to mark Python functions for JIT compilation. Pymothoa uses LLVM for the JIT ability. Comparing to writing C-extension to speedup Python, Pymothoa is less cumbersome and easier to distribute as the user does not need to compile the C-extensions.

Programming in the Pymothoa dialect is similar to writing in C. Variables must be declared and are statically typed. Despite a few extra constructs, the syntax is the same as raw Python code.

Key Features:
  * Use Python syntax for low-level C-like programming (no pointer).
  * Portable vector programming.
  * Colored error messages.

Limitations:
  * Does not support exception.
  * Does not support Python objects.
  * Only work on module-level function; not class methods.

Dependencies:
  * Python 2.6+
  * Tested with LLVM 3.1 (may also work for other version).