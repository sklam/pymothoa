import logging
import unittest
logging.basicConfig()

from pymothoa.compiler import function
from pymothoa.compiler_errors import *
from pymothoa.types import *
from pymothoa.dialect import *


@function(ret=Int, later=True)
def test_no_ret():
    pass

class Test(unittest.TestCase):
    def test_no_return_error(self):
        with self.assertRaises(CompilerError) as handle:
            test_no_ret.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(MissingReturnError))

if __name__ == '__main__':
    unittest.main()
