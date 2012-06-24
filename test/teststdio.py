import logging
#logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
from pymothoa.builtins import stdio
from pymothoa.types import *
from pymothoa.dialect import *

@function
def test_putchar():
    stdio.putchar(65) # A
    stdio.putchar(66) # B
    stdio.putchar(67) # C
    stdio.putchar(0x0D) # endline
    stdio.putchar(0x0A) # endline

def main():
    test_putchar()

if __name__ == '__main__':
    main()
