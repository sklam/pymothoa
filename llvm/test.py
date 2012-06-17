
from llvm_wrapper import *
jit = JITEngine()
dataty = TypeFactory.make_float()

fn = jit.make_function("myfunc", dataty, [dataty, dataty])
if not fn:
    raise RuntimeError("Invalid function")
    
bb = fn.append_basic_block('entry')

builder = Builder()

builder.insert_at(bb)

args = fn.arguments()

res = builder.fdiv(args[0], args[1])
bit = builder.fcmp(FCMP_OEQ, args[0], args[1])
builder.ret(res)

print '== verify', fn.name(), fn.verify()
print fn.dump()

jit.optimize(fn);

print '== verify JIT', jit.verify()
print fn.dump()

# cast resulting function pointer to ctypes
from ctypes import CFUNCTYPE, cast, c_int, c_int64, c_float
c_funcptr_t = CFUNCTYPE(c_float, c_float, c_float)
funcptr = cast( int( jit.get_pointer_to_function(fn) ), c_funcptr_t )
print funcptr(4, 2)
