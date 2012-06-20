from mamba.util.descriptor import Descriptor, instanceof

class LLVMValue(object):
    type = Descriptor(constant=True)

    __init__ = NotImplemented

class LLVMTempValue(LLVMValue):
    temp_value = Descriptor(constant=True)

    def __init__(self, val, ty):
        self.type = ty
        self.temp_value = val

    def value(self, builder):
        return self.temp_value

class LLVMTempPointer(LLVMValue):
    pointer = Descriptor(constant=True)

    def __init__(self, ptr, ty):
        self.type = ty
        self.pointer = ptr

class LLVMVariable(LLVMValue):
    pointer = Descriptor(constant=True)

    def __init__(self, name, ty, builder):
        self.type = ty
        self.pointer = builder.alloc(ty.type(), name)

    def value(self, builder):
        return builder.load(self.pointer)

class LLVMConstant(LLVMValue):
    constant = Descriptor(constant=True)

    def __init__(self, ty, val):
        self.type = ty
        self.constant = self.type.constant(val)

    def value(self, builder):
        return self.constant
