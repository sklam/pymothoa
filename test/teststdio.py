import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import default_module, function, declare_builtin
from pymothoa.builtins import stdio
from pymothoa.types import *
from pymothoa.dialect import *


putchar = declare_builtin(*stdio.putchar)

@function
def test_putchar():
    putchar(65) # A
    putchar(66) # B
    putchar(67) # C
    putchar(0x0D) # endline
    putchar(0x0A) # endline

def main():
    test_putchar()

if __name__ == '__main__':
    main()
