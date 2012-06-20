import logging

import types

def function(ret=types.Void, args=[]):
    def wrapper(func):
        assert type(func).__name__=='function', (
                '"%s" is not a function.'%func.__name__
        )

        from llvm_backend.function import LLVMFunction

        llvmfn = LLVMFunction(func, ret, args)
        llvmfn.compile()
        llvmfn.optimize()

        return llvmfn

    return wrapper

