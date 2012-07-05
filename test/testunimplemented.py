import logging
logging.basicConfig(level=logging.DEBUG)

from pymothoa.jit import JITModule
from pymothoa.types import *
from pymothoa.dialect import *


dummy = JITModule('testunimplemented')

@dummy.function(later=True)
def test_print():
    print 123

@dummy.function(later=True)
def test_string():
    'fodijafoidaj'
    'ojfdioajfoidaj'

#------------------------------------------------------------------------------
import unittest
from pymothoa.compiler_errors import *

class Test(unittest.TestCase):
    def test_print(self):
        with self.assertRaises(CompilerError) as handle:
            test_print.compile()

        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InternalError))

    def test_string(self):
        with self.assertRaises(CompilerError) as handle:
            test_string.compile()

        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InternalError))

if __name__ == '__main__':
    unittest.main()
