import logging
import ast, inspect

from pyon.descriptor import Descriptor, instanceof

from module import LLVMModuleManager
from backend import LLVMCodeGenerator
from types import *

logger = logging.getLogger(__name__)

class LLVMFunction(object):
    retty = Descriptor(constant=True)
    argtys = Descriptor(constant=True)

    code_python = Descriptor(constant=True)
    code_llvm = Descriptor(constant=True)

    c_funcptr_type = Descriptor(constant=True)
    c_funcptr = Descriptor(constant=True)

    manager = LLVMModuleManager() # class member

    def __init__(self, orig_func, retty, argtys):
        self.code_python = orig_func
        self.retty = LLVMType(retty)
        self.argtys = map(lambda X: LLVMType(X), argtys)

    def compile(self):
        from mamba.compiler_errors import CompilerError
        from mamba import terminal_helpers as term

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
            # Handle error and print useful information
            modname = func.func_globals['__name__']
            filename = func.func_globals['__file__']
            corrsource = inspect.getsourcelines(func)
            corrline = corrsource[0][e.line-1].rstrip()
            corrptr = '%s^\t(in %s:%d:%d)'%(
                            '-'*(e.col),
                            filename,
                            corrsource[1]+e.line-1,
                            e.col+1)
            template = '\n'.join([term.header('\nWhen compiling function "%s.%s":'),
                       term.fail('%s'),
                       '%s'])
            msg = template %(
                    modname,
                    func.func_name,
                    corrline,
                    corrptr,
                )

            raise CompilerError(e, msg)

        self.code_llvm = codegen.function
        self.code_llvm.verify()     # verify generated code

        logger.debug('Dump LLVM IR\n%s', self.code_llvm.dump())

    def optimize(self):
        self.manager.optimize(self.code_llvm)

        logger.debug('Optimized llvm ir:\n%s', self.code_llvm.dump())

    def assembly(self):
        return self.manager.dump_asm(self.code_llvm)


    def run_py(self, *args):
        return self.code_python(*args)

    def run_jit(self, *args):
        # Cast the arguments to corresponding types
        argvals = [aty.argument_adaptor(aval) for aty, aval in zip(self.argtys, args)]
        try:
            return self.c_funcptr(*argvals)
        except AttributeError: # Has not create binding to the function.
            # Obtain pointer to function from the JIT engine
            addr = self.manager.jit_engine.get_pointer_to_function(self.code_llvm)
            # Create binding with ctypes library
            from ctypes import CFUNCTYPE, cast
            c_argtys = map(lambda T: T.ctype(), self.argtys)
            c_retty = self.retty.ctype()
            self.c_funcptr_type = CFUNCTYPE(c_retty, *c_argtys)
            self.c_funcptr = cast( int(addr), self.c_funcptr_type )
            # Call the function
            return self.c_funcptr(*argvals)


    __call__ = run_jit
