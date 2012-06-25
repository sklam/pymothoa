import logging
import ast, inspect

from pymothoa.util.descriptor import Descriptor, instanceof
from pymothoa.compiler_errors import FunctionDeclarationError
from module import LLVMModule
from backend import LLVMCodeGenerator
from types import *

logger = logging.getLogger(__name__)

class LLVMFunction(object):

    ret = Descriptor(constant=True)
    args = Descriptor(constant=True)

    retty = Descriptor(constant=True)
    argtys = Descriptor(constant=True)

    code_python = Descriptor(constant=True)
    code_llvm = Descriptor(constant=True)

    c_funcptr_type = Descriptor(constant=True)
    c_funcptr = Descriptor(constant=True)

    manager = Descriptor(constant=True)

    _workarounds = Descriptor(constant=True)

    # wordarounds
    RET_BOOL_WORKAROUND='converts boolean return type to int8'
    ARG_BOOL_WORKAROUND='converts boolean argument type to int8'

    @classmethod
    def new(cls, module, orig_func, retty, argtys):

        self = cls()
        self.code_python = orig_func
        self.manager = module
        self.ret=retty
        self.args=argtys

        self._workarounds = set()

        # Take care of return type
        if retty is types.Bool: # boolean workaround
            # Change return type to 8-bit int
            self.retty = LLVMType(types.Int8)
            self._workarounds.add(self.RET_BOOL_WORKAROUND)
        else:
            self.retty = LLVMType(retty)

        # Take care of argument type
        self.argtys=[]
        for argty in argtys:
            if argty is types.Bool: # boolean workaround
                self.argtys.append(LLVMType(types.Int8))
                self._workarounds.add(self.ARG_BOOL_WORKAROUND)
            else:
                self.argtys.append(LLVMType(argty))

        return self

    @classmethod
    def new_declaration(cls, module, fname, retty, argtys):
        self = cls()
        self.manager = module
        self.retty = LLVMType(retty)
        self.argtys = map(lambda X: LLVMType(X), argtys)
        self.ret=retty
        self.args=argtys

        # declare
        retty = self.retty.type()
        argtys = map(lambda X: X.type(), self.argtys)
        self.code_llvm = self.manager.jit_engine.make_function(fname, retty, argtys)
        if not self.code_llvm.valid():
            raise FunctionDeclarationError(cls.manager.jit_engine.last_error())

        self.compile = NotImplemented
        self.run_py = NotImplemented
        self.run_jit = NotImplemented
        self.assembly = NotImplemented

        return self

    def compile(self):
        from pymothoa.compiler_errors import CompilerError, wrap_by_function


        func = self.code_python
        source = inspect.getsource(func)

        logger.debug('Compiling function: %s', func.__name__)

        tree = ast.parse(source)

        assert type(tree).__name__=='Module'
        assert len(tree.body)==1

        # Code generation for LLVM
        try:
            codegen = LLVMCodeGenerator(
                            self.manager.jit_engine,
                            self.retty,
                            self.argtys,
                            symbols=func.func_globals
                        )
            codegen.visit(tree.body[0])
        except CompilerError as e:
            raise wrap_by_function(e, func)

        self.code_llvm = codegen.function
        self.code_llvm.verify()     # verify generated code

        logger.debug('Dump LLVM IR\n%s', self.code_llvm.dump())

    def assembly(self):
        return self.manager.dump_asm(self.code_llvm)

    def prepare_pointer_to_function(self):
        '''Obtain pointer to function from the JIT engine'''
        addr = self.manager.jit_engine.get_pointer_to_function(self.code_llvm)
        # Create binding with ctypes library
        from ctypes import CFUNCTYPE, cast
        c_argtys = map(lambda T: T.ctype(), self.argtys)
        c_retty = self.retty.ctype()
        self.c_funcptr_type = CFUNCTYPE(c_retty, *c_argtys)
        self.c_funcptr = cast( int(addr), self.c_funcptr_type )

    def run_py(self, *args):
        return self.code_python(*args)

    def run_jit(self, *args):
        # Cast the arguments to corresponding types
        argvals = [aty.argument_adaptor(aval) for aty, aval in zip(self.argtys, args)]
        try:
            retval = self.c_funcptr(*argvals)
        except AttributeError: # Has not create binding to the function.
            self.prepare_pointer_to_function()
            # Call the function
            retval = self.c_funcptr(*argvals)
        # Apply any workaround to the return value
        if self.RET_BOOL_WORKAROUND in self._workarounds:
            retval = bool(retval)

        return retval


    __call__ = run_jit
