from pymothoa.util.descriptor import Descriptor, instanceof

import llvm # binding

class LLVMModuleManager(object):
    jit_engine = Descriptor(constant=True)

    def __init__(self):
        # This is a singleton class.
        # Check to ensure
        if hasattr(type(self), '__inst_ct'):
            raise RuntimeError('%s is a singleton class.'%type(self))
        else:
            type(self).__inst_ct=1
        from default_passes import DEFAULT_PASSES
        self.jit_engine = llvm.JITEngine(DEFAULT_PASSES, True)

    def optimize(self, fn):
        self.jit_engine.optimize(fn)
        fn.verify()

    def dump_asm(self, fn):
        return self.jit_engine.dump_asm(fn)

