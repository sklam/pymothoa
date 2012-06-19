import ctypes

from pyon.descriptor import Descriptor, instanceof

from mamba import types
import llvm # binding


class LLVMType(object):

    def __new__(cls, datatype):
        TYPE_MAP = {
            types.Void      : LLVMVoid,
            types.Int32     : LLVMInt32,
            types.Int64     : LLVMInt64,
            types.Float     : LLVMFloat,
            types.Double    : LLVMDouble,
        }
        try:
            return object.__new__(TYPE_MAP[datatype])
        except TypeError:
            assert type(datatype) is list
            assert len(datatype) == 1
            elemtype = datatype[0]
            obj = object.__new__(LLVMUnboundedArray)
            obj.elemtype = LLVMType(elemtype)
            return obj

class LLVMVoid(types.Void):
    def ctype(self):
        return None

    def type(self):
        return llvm.TypeFactory.make_void()

class LLVMBasicIntMixin(object):

    def argument_adaptor(self, val):
        return val

    def ctype(self):
        mapping = {
            32: ctypes.c_int32,
            64: ctypes.c_int64,
        }
        return mapping[self.bitsize]

    def type(self):
        return llvm.TypeFactory.make_int(self.bitsize)

    def constant(self, val):
        if type(val) is not int:
            raise TypeError(type(val))
        else:
            return llvm.ConstantFactory.make_int(self.type(), val)

    def cast(self, old, builder):
        if old.type == self:
            return old.value(builder)
        elif isinstance(old.type, types.GenericInt):
            assert old.type.bitsize != self.bitsize
            val = old.value(builder)
            return builder.icast(val, self.type(), self.signed)
        elif isinstance(old.type, types.GenericReal):
            val = old.value(builder)
            return builder.fptosi(val, self.type())
        else:
            print 'cast %s -> %s'%(old.type, self)

        assert False

    def op_add(self, lhs, rhs, builder):
        return builder.add(lhs, rhs)

    def op_sub(self, lhs, rhs, builder):
        return builder.sub(lhs, rhs)

    def op_mult(self, lhs, rhs, builder):
        return builder.mul(lhs, rhs)

    def op_div(self, lhs, rhs, builder):
        return builder.sdiv(lhs, rhs)

    def op_lte(self, lhs, rhs, builder):
        return builder.icmp(llvm.ICMP_SLE, lhs, rhs)

    def __eq__(self, other):
        return type(self) is type(other)

class LLVMBasicFloatMixin(object):

    def argument_adaptor(self, val):
        return val

    def ctype(self):
        return ctypes.c_float

    def type(self):
        return llvm.TypeFactory.make_float()

    def constant(self, val):
        return llvm.ConstantFactory.make_real(self.type(), val)

    def cast(self, old, builder):
        if old.type == self:
            return old.value(builder)
        elif isinstance(old.type, types.GenericInt):
            val = old.value(builder)
            return builder.sitofp(val, self.type())
        elif isinstance(old.type, types.GenericReal):
            val = old.value(builder)
            return builder.fcast(val, self.type())
        else:
            print 'cast %s -> %s'%(old.type, self)

        assert False

    def op_add(self, lhs, rhs, builder):
        return builder.fadd(lhs, rhs)

    def op_sub(self, lhs, rhs, builder):
        return builder.fsub(lhs, rhs)

    def op_mult(self, lhs, rhs, builder):
        return builder.fmul(lhs, rhs)

    def op_div(self, lhs, rhs, builder):
        return builder.fdiv(lhs, rhs)

    def op_lte(self, lhs, rhs, builder):
        return builder.fcmp(llvm.FCMP_OLE, lhs, rhs)

    def __eq__(self, other):
        return type(self) is type(other)


class LLVMBasicDoubleMixin(LLVMBasicFloatMixin):
    def ctype(self):
        return ctypes.c_double

    def type(self):
        return llvm.TypeFactory.make_double()

class LLVMInt32(types.Int32, LLVMBasicIntMixin):
    pass

class LLVMInt64(types.Int64, LLVMBasicIntMixin):
    pass

class LLVMFloat(types.Float, LLVMBasicFloatMixin):
    pass

class LLVMDouble(types.Float, LLVMBasicDoubleMixin):
    pass

class LLVMUnboundedArray(types.GenericUnboundedArray):

    elemtype = Descriptor(constant=True, constrains=instanceof(types.BuiltinType))

    def ctype(self):
        return ctypes.POINTER(self.elemtype.ctype())

    def type(self):
        return llvm.TypeFactory.make_pointer(self.elemtype.type())

    def argument_adaptor(self, val):
        from numpy import ndarray
        if isinstance(val, ndarray):
            assert val.dtype == self.elemtype.ctype()
            return val.ctypes.data_as(self.ctype())
        raise TypeError(type(val))
