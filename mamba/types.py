class Type(object):
    pass

class BuiltinType(Type):
    pass

class Void(BuiltinType):
    rank = 0

    @classmethod
    def make_llvm(cls):
        from llvm.core import Type
        return Type.void()

class Int(BuiltinType):
    rank = 10
    bitsize = 32
    signed = True
    
    @classmethod
    def make_llvm(cls):
        from llvm.core import Type
        return Type.int(cls.bitsize)

    @classmethod
    def to_llvm(cls, val):
        return val.as_int_signed()

    @classmethod
    def from_llvm(cls, val):
        from llvm.ee import GenericValue
        return GenericValue.int_signed(cls.make_llvm(), val)

    @classmethod
    def cast_llvm(cls, val, sty, builder):
        assert sty is not cls
        if issubclass(sty, Int):
            if cls.rank > sty.rank:
                #promote
                return builder.sext(val, cls.make_llvm())
            else:
                #demote
                return builder.trunc(val, cls.make_llvm())
        else:
            assert False
    
Int32=Int

class Int64(Int):
    rank = 11
    bitsize = 64

class TypeAdaptor(object):
    __slots__ =  '__backend'

    def __init__(self, backend):
        self.__backend = backend

    @property
    def backend(self):
        return self.__backend

    def make(self, ty):
        fn = getattr(ty, 'make_%s'%self.backend)
        return fn()

    def recv(self, ty, val):
        fn = getattr(ty, 'to_%s'%self.backend)
        return fn(val)

    def send(self, ty, val):
        fn = getattr(ty, 'from_%s'%self.backend)
        return fn(val)

    def cast(self, ty, val, srcty, **kwargs):
        fn = getattr(ty, 'cast_%s'%self.backend)
        return fn(val, srcty, **kwargs)
