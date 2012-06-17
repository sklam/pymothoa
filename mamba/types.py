class Type(object):    
    __init__ = NotImplemented

class BuiltinType(Type):
    def coerce(self, other):
        '''Returns the type that has a higher rank.
        '''
        if self.rank > other.rank:
            return self
        else:
            return other

class Void(BuiltinType):
    rank = 0

class GenericInt(BuiltinType):
    pass

class Int32(GenericInt):
    rank = 10
    bitsize = 32
    signed = True

class Int64(GenericInt):
    rank = 11
    bitsize = 64
    signed = True

def _determinte_native_int_size():
    from ctypes import c_int, c_int32, c_int64
    if c_int is c_int32: 
        return Int32
    elif c_int is c_int64: 
        return Int64
    else:
        raise NotImplementedError('Integer size other than 32/64-bit?')
        
Int=_determinte_native_int_size()

class GenericReal(BuiltinType):
    pass

class Float(GenericReal):
    rank = 20

class Double(GenericReal):
    rank = 30

