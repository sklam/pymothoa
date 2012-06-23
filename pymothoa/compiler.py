import logging, inspect
import types

def function(ret=types.Void, args=[], later=False, opt=True):
    def wrapper(func):
        assert type(func).__name__=='function', (
                '"%s" is not a function.'%func.__name__
        )
        # There is only one backend at this point.
        from llvm_backend.function import LLVMFunction

        llvmfn = LLVMFunction(func, ret, args)
        if not later: # compile later flag    
            llvmfn.compile()
            if opt: # do optimization flag
                llvmfn.optimize()

        return llvmfn
    return wrapper

