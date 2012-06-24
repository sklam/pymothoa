import types

def function(func=None, ret=types.Void, args=[], later=False, opt=True):
    def wrapper(func):
        assert type(func).__name__=='function', (
                '"%s" is not a function.'%func.__name__
        )
        # There is only one backend at this point.
        from llvm_backend.function import LLVMFunction

        llvmfn = LLVMFunction.new(func, ret, args)
        if not later: # compile later flag
            llvmfn.compile()
            if opt: # do optimization flag
                llvmfn.optimize()

        return llvmfn

    if func is None:
        return wrapper
    else:
        return wrapper(func)

def declaration(ret=types.Void, args=[]):
    def wrapper(func):
        from llvm_backend.function import LLVMFunction
        namespace = func.func_globals['__name__']
        realname = '.'.join([namespace, func.__name__])
        return LLVMFunction.new_declaration(realname, ret, args)
    return wrapper

def builtin_declaration(ret=types.Void, args=[], prefix=''):
    def wrapper(func):
        from llvm_backend.function import LLVMFunction
        realname = '%s%s'%(prefix, func.__name__)
        return LLVMFunction.new_declaration(realname, ret, args)
    return wrapper
