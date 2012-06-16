class Type(object):
    
    def __new__(cls, backend):
        return object.__new__(backend.configure(cls))
    
    def __init__(self, backend):
        pass

class BuiltinType(Type):
    def coerce(self, other):
        if self.rank > other.rank:
            return self
        else:
            return other

class Void(BuiltinType):
    rank = 0

class Int(BuiltinType):
    rank = 10
    bitsize = 32
    signed = True

Int32=Int

class Int64(Int):
    rank = 11
    bitsize = 64

class Float(BuiltinType):
    rank = 20

