import logging
import ast, inspect
import ctypes
from compiler import *

from pyon.descriptor import Descriptor, instanceof

import llvm
import types

logger = logging.getLogger(__name__)

class LLVMModuleManager(object):
    jit_engine = Descriptor(constant=True)

    def __init__(self):
        # This is a singleton class.
        # Check to ensure
        if hasattr(type(self), '__inst_ct'):
            raise RuntimeError('%s is a singleton class.'%type(self))
        else:
            type(self).__inst_ct=1
        self.jit_engine = llvm.JITEngine()

    def optimize(self, fn):
        self.jit_engine.optimize(fn)
        fn.verify()

    def dump_asm(self, fn):
        return self.jit_engine.dump_asm(fn)

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

class LLVMFunction(object):
    retty = Descriptor(constant=True)
    argtys = Descriptor(constant=True)

    code_python = Descriptor(constant=True)
    code_llvm = Descriptor(constant=True)

    c_funcptr_type = Descriptor(constant=True)
    c_funcptr = Descriptor(constant=True)

    manager = LLVMModuleManager() # class member

    def __init__(self, orig_func, retty, argtys):
        self.code_python = orig_func
        self.retty = LLVMType(retty)
        self.argtys = map(lambda X: LLVMType(X), argtys)

    def compile(self):

        func = self.code_python
        source = inspect.getsource(func)

        logger.debug('Compiling function: %s', func.__name__)

        tree = ast.parse(source)

        assert type(tree).__name__=='Module'
        assert len(tree.body)==1

        # Code generation for LLVM
        codegen = LLVMCodeGenerator(
                        self.manager.jit_engine,
                        self.retty,
                        self.argtys,
                        symbols=func.func_globals
                    )
        codegen.visit(tree.body[0])

        self.code_llvm = codegen.function
        self.code_llvm.verify()     # verify generated code

        logger.debug('Dump LLVM IR\n%s', self.code_llvm.dump())

    def optimize(self):
        self.manager.optimize(self.code_llvm)

        logger.debug('Optimized llvm ir:\n%s', self.code_llvm.dump())

    def assembly(self):
        return self.manager.dump_asm(self.code_llvm)

    def __call__(self, *args):
        return self.code_python(*args)

    def jit(self, *args):
        # Cast the arguments to corresponding types
        argvals = [aty.argument_adaptor(aval) for aty, aval in zip(self.argtys, args)]
        try:
            return self.c_funcptr(*argvals)
        except AttributeError: # Has not create binding to the function.
            # Obtain pointer to function from the JIT engine
            addr = self.manager.jit_engine.get_pointer_to_function(self.code_llvm)
            # Create binding with ctypes library
            from ctypes import CFUNCTYPE, cast
            c_argtys = map(lambda T: T.ctype(), self.argtys)
            c_retty = self.retty.ctype()
            self.c_funcptr_type = CFUNCTYPE(c_retty, *c_argtys)
            self.c_funcptr = cast( int(addr), self.c_funcptr_type )
            # Call the function
            return self.c_funcptr(*argvals)

class LLVMCodeGenerator(ast.NodeVisitor):
    jit_engine    = Descriptor(constant=True)
    retty         = Descriptor(constant=True)
    argtys        = Descriptor(constant=True)
    function      = Descriptor(constant=True)
    symbols       = Descriptor(constant=True, constrains=instanceof(dict))

    def __init__(self, jit_engine, retty, argtys, symbols):
        super(LLVMCodeGenerator, self).__init__()
        self.jit_engine = jit_engine
        self.retty = retty
        self.argtys = argtys
        # symbol table
        self.symbols = symbols.copy()

    def visit_FunctionDef(self, node):

        retty = self.retty.type()
        argtys = map(lambda X: X.type(), self.argtys)

        self.function = self.jit_engine.make_function(node.name, retty, argtys)
        self.symbols[self.function.name] = self.function
        assert self.function.name()==node.name, (self.function.name(), node.name)

        # make basic block
        bb_entry = self.function.append_basic_block("entry")
        self.__blockcounter = 0

        # make instruction builder
        self.builder = llvm.Builder()
        self.builder.insert_at(bb_entry)

        # build arguments
        self.visit(node.args)

        # build body
        for stmt in node.body:
            self.visit(stmt)
        else:
            if not self.builder.is_block_closed():
                if isinstance(self.retty, types.Void): # no return
                    self.builder.ret_void()
                else:
                    raise MissingReturnError(self.function.name)

    def visit_arguments(self, node):
        '''Function arguments.
        '''
        assert not node.vararg, 'Variable argument not yet supported.'
        assert not node.kwarg, 'Does not support keyword argument'
        assert not node.defaults, 'Does not support default argument'

        fn_args = self.function.arguments()
        for i, arg in enumerate(node.args):
            assert isinstance(arg.ctx, ast.Param)
            name = arg.id
            var = LLVMVariable(name, self.argtys[i], self.builder)
            self.builder.store(fn_args[i], var.pointer)
            self.symbols[name] = var

    def visit_Call(self, node):
        import dialect
        fn = self.visit(node.func)

        if type(fn) is type and issubclass(fn, dialect.Construct):
            if issubclass(fn, dialect.var):
                assert not node.args
                for kw in node.keywords:
                    ty = self.visit(kw.value)
                    name = kw.arg
                    self.declare(name, ty)
                return
            else:
                assert False
        elif isinstance(fn, LLVMFunction):
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            arg_values = map(lambda X: LLVMTempValue(X.value(self.builder), X.type), args)
            # cast types
            for i, argty in enumerate(fn.argtys):
                arg_values[i] = argty.cast(arg_values[i], self.builder)

            out = self.builder.call(fn.code_llvm, arg_values)
            return LLVMTempValue(out, fn.retty)
        elif fn is self.function:
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            arg_values = map(lambda X: LLVMTempValue(X.value(self.builder), X.type), args)
            # cast types
            for i, argty in enumerate(self.argtys):
                arg_values[i] = argty.cast(arg_values[i], self.builder)

            out = self.builder.call(fn, arg_values)
            return LLVMTempValue(out, self.retty)

        assert False, fn

    def visit_Expr(self, node):
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            try: # lookup in the symbol table
                val = self.symbols[node.id]
            except KeyError: # does not exist
                if node.id == self.function.name():
                    return self.function
                raise UndefinedSymbolError(node.id)
            else: # load from stack
                return val
        else:
            assert isinstance(node.ctx, ast.Store)
            try:
                return self.symbols[node.id]
            except KeyError:
                raise UndefinedSymbolError(node.id)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            value = self.visit(node.value)
            return getattr(value, node.attr)
        else:
            assert False

    def visit_If(self, node):
        test = self.visit(node.test)

        bb_if = self.new_basic_block('if')
        bb_else = self.new_basic_block('else')
        bb_endif = self.new_basic_block('endif')
        is_endif_reachable = False

        self.builder.cond_branch(test, bb_if, bb_else)


        # true branch
        self.builder.insert_at(bb_if)
        for stmt in node.body:
            self.visit(stmt)
        else:
            if not self.builder.is_block_closed():
                self.builder.branch(bb_endif)
                is_endif_reachable=True

        # false branch
        self.builder.insert_at(bb_else)
        for stmt in node.orelse:
            self.visit(stmt)
        else:
            if not self.builder.is_block_closed():
                self.builder.branch(bb_endif)
                is_endif_reachable=True

        # endif
        self.builder.insert_at(bb_endif)
        if not is_endif_reachable:
            self.builder.unreachable()

    def visit_For(self, node):
        assert not node.orelse, 'Else in for-loop is not supported yet'

        iternode = node.iter
        assert isinstance(iternode, ast.Call)
        looptype = iternode.func.id
        assert looptype in ['range', 'xrange']
        assert len(iternode.args) in [1,2]

        counter_ptr = self.declare(node.target.id, types.Int)

        iternode_arg_N = len(iternode.args)
        if iternode_arg_N==1:
            zero = LLVMConstant(LLVMType(types.Int), 0)
            initcount = zero
            endcountpos = 0
        elif iternode_arg_N==2:
            initcount = self.visit(iternode.args[0])
            endcountpos = 1
        else:
            assert False

        endcount = self.visit(iternode.args[endcountpos]).value(self.builder)
        self.builder.store(initcount.value(self.builder), counter_ptr.pointer)

        bb_cond = self.new_basic_block('loopcond')
        bb_body = self.new_basic_block('loopbody')
        bb_incr = self.new_basic_block('loopincr')
        bb_exit = self.new_basic_block('loopexit')

        self.builder.branch(bb_cond)

        # condition
        self.builder.insert_at(bb_cond)
        test = self.builder.icmp(llvm.ICMP_SLT, counter_ptr.value(self.builder), endcount)
        self.builder.cond_branch(test, bb_body, bb_exit)

        # body
        self.builder.insert_at(bb_body)

        for stmt in node.body:
            self.visit(stmt)
        else:
            self.builder.branch(bb_incr)

        # incr
        self.builder.insert_at(bb_incr)
        one = LLVMConstant(LLVMType(types.Int), 1)
        counter_next = self.builder.add(counter_ptr.value(self.builder), one.value(self.builder))
        self.builder.store(counter_next, counter_ptr.pointer)
        self.builder.branch(bb_cond)

        # exit
        self.builder.insert_at(bb_exit)


    def visit_Compare(self, node):
        assert len(node.ops)==1
        assert len(node.comparators)==1
        lhs = self.visit(node.left)
        rhs = self.visit(node.comparators[0])
        op  = type(node.ops[0])

        ty = lhs.type.coerce(rhs.type)
        lval = ty.cast(lhs, self.builder)
        rval = ty.cast(rhs, self.builder)

        fn = getattr(ty, 'op_%s'%op.__name__.lower())

        return fn(lval, rval, self.builder)

    def visit_Return(self, node):
        value = self.visit(node.value)
        casted = self.retty.cast(value, self.builder)
        self.builder.ret(casted)

    def visit_Assign(self, node):
        assert len(node.targets)==1, 'Not yet implemented multi target in assignment'
        target = self.visit(node.targets[0])
        value = self.visit(node.value)
        casted = target.type.cast(value, self.builder)
        self.builder.store(casted, target.pointer)

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = type(node.op)

        ty = lhs.type.coerce(rhs.type)
        lval = ty.cast(lhs, self.builder)
        rval = ty.cast(rhs, self.builder)

        fn = getattr(ty, 'op_%s'%op.__name__.lower())

        return LLVMTempValue(fn(lval, rval, self.builder), ty)

    def visit_Subscript(self, node):
        assert isinstance(node.slice, ast.Index)
        ptr = self.visit(node.value)
        idx = self.visit(node.slice.value)
        ptr_val = ptr.value(self.builder)
        idx_val = idx.value(self.builder)
        ptr_offset = self.builder.gep(ptr_val, idx_val)
        if isinstance(node.ctx, ast.Store):
            return LLVMTempPointer(ptr_offset, ptr.type.elemtype)
        else:
            assert isinstance(node.ctx, ast.Load)
            return LLVMTempValue(self.builder.load(ptr_offset), ptr.type.elemtype)

    def visit_Num(self, node):
        if type(node.n) is int:
            return LLVMConstant(LLVMType(types.Int), node.n)
        elif type(node.n) is float:
            return LLVMConstant(LLVMType(types.Double), node.n)

    def visit(self, node):
        try:
            fn = getattr(self, 'visit_%s' % type(node).__name__)
        except AttributeError:
            logger.debug('Unhandled visit to %s', ast.dump(node))
            raise
            # return super(LLVMCodeGenerator, self).visit(node)
        else:
            return fn(node)

    def declare(self, name, ty):
        realty = LLVMType(ty)
        if name in self.symbols:
            raise VariableRedeclarationError(name)

        self.symbols[name] = var = LLVMVariable(name, realty, self.builder)
        return var

    def new_basic_block(self, name='uname'):
        self.__blockcounter += 1
        return self.function.append_basic_block('%s_%d'%(name, self.__blockcounter))

