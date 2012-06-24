import logging
import unittest
logging.basicConfig(level=logging.DEBUG)

from pymothoa.compiler import function
from pymothoa.compiler_errors import *
from pymothoa.types import *
from pymothoa.dialect import *


@function(ret=Int, later=True)
def test_no_ret():
    pass

@function(later=True)
def test_no_var_decl():
    A + 1

@function(later=True)
def test_wrong_ret():
    return 123

@function(later=True)
def test_dup_var_decl():
    var ( A = Int )
    var ( A = Float )

@function(later=True)
def test_invalid_subscript():
    var ( A = Int )
    A[0]

@function(later=True)
def test_invalid_vector_ctor():
    var ( A = Vector(Int) )

@function(later=True)
def test_invalid_vector_ctor_2():
    var ( A = Vector(Int, 0) )

@function(later=True)
def test_invalid_vector_ctor_3():
    var ( A = Int )
    var ( vec = Vector(A, 0) )

@function(args=[ Array(Float) ])
def test_invalid_array_typecode(A):
    pass

@function(later=True)
def test_invalid_array_ctor():
    var ( array = Array(Int) )


class Test(unittest.TestCase):
    def test_no_return_error(self):
        with self.assertRaises(CompilerError) as handle:
            test_no_ret.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(MissingReturnError))

    def test_no_var_decl(self):
        with self.assertRaises(CompilerError) as handle:
            test_no_var_decl.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(UndefinedSymbolError))

    def test_wrong_ret(self):
        with self.assertRaises(CompilerError) as handle:
            test_wrong_ret.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidReturnError))

    def test_dup_var_decl(self):
        with self.assertRaises(CompilerError) as handle:
            test_dup_var_decl.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(VariableRedeclarationError))

    def test_invalid_subscript(self):
        with self.assertRaises(CompilerError) as handle:
            test_invalid_subscript.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidSubscriptError))

    def test_invalid_vector_ctor(self):
        with self.assertRaises(CompilerError) as handle:
            test_invalid_vector_ctor.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidUseOfConstruct))

    def test_invalid_vector_ctor_2(self):
        with self.assertRaises(CompilerError) as handle:
            test_invalid_vector_ctor_2.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidUseOfConstruct))

    def test_invalid_vector_ctor_3(self):
        with self.assertRaises(CompilerError) as handle:
            test_invalid_vector_ctor_3.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidUseOfConstruct))

    def test_invalid_array_typecode(self):
        from array import array
        A = array('i', range(10))
        with self.assertRaises(TypeError) as handle:
            test_invalid_array_typecode(A)
        print 'Invalid argument of test_invalid_array_typecode()'
        print handle.exception

    def test_invalid_array_ctor(self):
        with self.assertRaises(CompilerError) as handle:
            test_invalid_array_ctor.compile()
        print handle.exception
        self.assertTrue(handle.exception.is_due_to(InvalidUseOfConstruct))

if __name__ == '__main__':
    unittest.main()
