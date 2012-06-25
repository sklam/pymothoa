'''
Note: LLVM does not permit inter module call. Either the caller module is
linked with the callee module. Or, a function pointer is brought from the callee
to the caller. (Any alternative?)
'''

from pymothoa.util.descriptor import Descriptor, instanceof
from default_passes import DEFAULT_PASSES

import llvm # binding

class LLVMModule(object):
    jit_engine = Descriptor(constant=True)

    def __init__(self, name, passes=DEFAULT_PASSES):
        self.jit_engine = llvm.JITEngine(name, DEFAULT_PASSES, True)

    def optimize(self):
        self.jit_engine.optimize()

    def verify(self):
        self.jit_engine.verify()

    def dump_asm(self, fn):
        return self.jit_engine.dump_asm(fn)

    def dump(self):
        return self.jit_engine.dump()

    def new_function(self, fnobj, ret, args):
        from function import LLVMFunction
        return LLVMFunction.new(self, fnobj, ret, args)

    def new_declaration(self, fname, ret, args):
        from function import LLVMFunction
        return LLVMFunction.new_declaration(self, fname, ret, args)

