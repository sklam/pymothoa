from pymothoa.compiler import builtin_declaration
from pymothoa.types import *

@builtin_declaration(ret=Int, args=[Int])
def putchar(ch):
    pass
