import logging
import ast, inspect

from llvm.core import *

from pyon.descriptor import Descriptor, instanceof

import types

logger = logging.getLogger(__name__)

class LLVMModuleManager(object):
    module       = Descriptor(constant=True)
    pass_manager = Descriptor(constant=True)
    executor     = Descriptor(constant=True)

    def __init__(self):
        # This is a singleton class.
        # Check to ensure
        if hasattr(type(self), '__inst_ct'):
            raise RuntimeError('%s is a singleton class.'%type(self))
        else:
            type(self).__inst_ct=1

        # LLVM specific
        from llvm.core import Module
        from llvm import passes
        from llvm.ee import ExecutionEngine

        # Make LLVM module for JIT code
        mod = self.module = Module.new('mamba.default')

        # Make JIT executor or interpreter (depending on the platform)
        exe = self.executor = ExecutionEngine.new(mod)

        # Make LLVM function pass manager for optimization
        pm = self.pass_manager = passes.FunctionPassManager.new(mod)

        # For reference:
        #   http://llvm.org/docs/Passes.html
        #   llvm-as < /dev/null | opt -O2 -disable-output -debug-pass=Arguments

        pm.add(exe.target_data) # register target data layout

        opt_passes = [
            passes.PASS_PROMOTE_MEMORY_TO_REGISTER,
            passes.PASS_INSTRUCTION_COMBINING,
            passes.PASS_REASSOCIATE,
            passes.PASS_GVN,
            passes.PASS_CFG_SIMPLIFICATION,
            passes.PASS_TAIL_CALL_ELIMINATION,
        ]

        for opt_pass in opt_passes:
            pm.add(opt_pass)

        pm.initialize()
        
    def optimize(self, fn):
        self.pass_manager.run(fn)
        fn.verify()
        
class LLVMTypeEngine(object):
    @classmethod
    def configure(cls, datatype):
        return {
            types.Int   : LLVMInt,
            types.Int64 : LLVMInt64,
            types.Float : LLVMFloat,
        }[datatype]

class LLVMBasicIntMixin(object):
    def type(self):
        return Type.int(self.bitsize)
        
    def constant(self, val):
        if type(val) is not int:
            raise TypeError(type(val))
        else:
            return Constant.int(self.type(), val)
            
    def cast(self, old, builder):
        if old.type == self:
            return old.value(builder)
        elif isinstance(old.type, types.Int):
            assert old.type.bitsize != self.bitsize
            val = old.value(builder)
            if old.type.bitsize > self.bitsize:
                return builder.trunc(val, self.type())
            else:
                return builder.sext(val, self.type())                
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
        return builder.icmp(ICMP_SLE, lhs, rhs)
        
    def __eq__(self, other):
        return type(self) is type(other)
    
    def send(self, val):
        from llvm.ee import GenericValue
        return GenericValue.int_signed(self.type(), val)
        
    def recv(self, val):
        return val.as_int_signed()


class LLVMBasicFloatMixin(object):
    def type(self):
        return Type.double()
        
    def constant(self, val):
        if type(val) is float:
            return Constant.real(self.type(), val)
        elif type(val) in [int, long]:
            return Constant.int(self.type(), val)
        else:
            raise TypeError(type(val))
            
    def cast(self, old, builder):
        if old.type == self:
            return old.value(builder)
        elif isinstance(old.type, types.Int):
            val = old.value(builder)
            return builder.sitofp(val, self.type())
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
        return builder.fcmp(FCMP_OLE, lhs, rhs)
        
    def __eq__(self, other):
        return type(self) is type(other)
    
    def send(self, val):
        from llvm.ee import GenericValue
        return GenericValue.real(self.type(), val)
        
    def recv(self, val):
        return val.as_real(self.type())
        

class LLVMInt(types.Int, LLVMBasicIntMixin):
    pass
    
class LLVMInt64(types.Int64, LLVMBasicIntMixin):
    pass
    
class LLVMFloat(types.Float, LLVMBasicFloatMixin):
    pass

class LLVMValue(object):
    type = Descriptor(constant=True)

    __init__ = NotImplemented
    
class LLVMTempValue(object):
    temp_value = Descriptor(constant=True)
    
    def __init__(self, val, ty):
        self.type = ty
        self.temp_value = val
    
    def value(self, builder):
        return self.temp_value
    
class LLVMVariable(LLVMValue):
    pointer = Descriptor(constant=True)
    
    def __init__(self, name, ty, builder):
        self.type = ty
        self.pointer = builder.alloca(ty.type(), name=name)    
        
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

    manager = LLVMModuleManager() # class member

    def __init__(self, orig_func, retty, argtys):
        self.code_python = orig_func
        self.retty = retty(LLVMTypeEngine)
        self.argtys = map(lambda X: X(LLVMTypeEngine), argtys)

    def compile(self):

        func = self.code_python
        source = inspect.getsource(func)

        logger.info('Compiling function: %s', func.__name__)

        tree = ast.parse(source)

        assert type(tree).__name__=='Module'
        assert len(tree.body)==1

        # Code generation for LLVM
        codegen = LLVMCodeGenerator(
                        self.manager.module,
                        self.retty,
                        self.argtys,
                        symbols=func.func_globals
                    )
        codegen.visit(tree.body[0])

        self.code_llvm = codegen.function
        self.code_llvm.verify()     # verify generated code

        logger.debug('Dump LLVM IR\n%s', self.code_llvm)

    def optimize(self):
        self.manager.optimize(self.code_llvm)

        logger.debug('Optimized llvm ir:\n%s', self.code_llvm)

    def __call__(self, *args):
        return self.code_python(*args)

    def jit(self, *args):
        args = [self.argtys[i].send(arg) for i, arg in enumerate(args)]

        retval = self.manager.executor.run_function(self.code_llvm, args)
        return self.retty.recv(retval)

class LLVMCodeGenerator(ast.NodeVisitor):
    module        = Descriptor(constant=True)
    retty         = Descriptor(constant=True)
    argtys        = Descriptor(constant=True)
    function      = Descriptor(constant=True)
    symbols       = Descriptor(constant=True, constrains=instanceof(dict))

    def __init__(self, module, retty, argtys, symbols):
        super(LLVMCodeGenerator, self).__init__()
        self.module = module
        self.retty = retty
        self.argtys = argtys
        # symbol table
        self.symbols = symbols.copy()

    def visit_FunctionDef(self, node):
        fnty = Type.function(self.retty.type(), map(lambda X: X.type(), self.argtys))
        self.function =  self.module.add_function(fnty, node.name)
        self.symbols[self.function.name] = self.function        
        
        # make basic block
        bb_entry = self.function.append_basic_block("entry")
        self.__blockcounter = 0

        # make instruction builder
        self.builder = Builder.new(bb_entry)

        # build arguments
        self.visit(node.args)

        # build body
        for stmt in node.body:
            self.visit(stmt)
        else:
            if not self.is_properly_close_basicblock():
                if self.retty == Type.void(): # no return
                    self.builder.ret_void()
                else:
                    raise MissingReturnError(self.function.name)

    def visit_arguments(self, node):
        '''Function arguments.
        '''
        assert not node.vararg, 'Variable argument not yet supported.'
        assert not node.kwarg, 'Does not support keyword argument'
        assert not node.defaults, 'Does not support default argument'

        for i, arg in enumerate(node.args):
            assert isinstance(arg.ctx, ast.Param)
            name = arg.id
            self.function.args[i].name = name+'.arg'
            var = LLVMVariable(name, self.argtys[i], self.builder)
            self.builder.store(self.function.args[i], var.pointer)
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
            arg_values = map(lambda X: X.value(self.builder), args)
            out = self.builder.call(fn.code_llvm, arg_values)
            return LLVMTempValue(out, fn.retty)
        elif fn is self.function:
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            arg_values = map(lambda X: X.value(self.builder), args)
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
                raise UndefinedSymbolError(node.id)
            else: # load from stack
                if isinstance(val, Instruction):
                    out = self.builder.load(val)
                    self.copy_typeinfo(out, val)
                    return out
                else:
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

        self.builder.cbranch(test, bb_if, bb_else)


        # true branch
        self.builder.position_at_end(bb_if)
        for stmt in node.body:
            self.visit(stmt)
        else:
            if not self.is_properly_close_basicblock():
                self.builder.branch(bb_endif)
                is_endif_reachable=True

        # false branch
        self.builder.position_at_end(bb_else)
        for stmt in node.orelse:
            self.visit(stmt)
        else:
            if not self.is_properly_close_basicblock():
                self.builder.branch(bb_endif)
                is_endif_reachable=True

        # endif
        self.builder.position_at_end(bb_endif)
        if not is_endif_reachable:
            self.builder.unreachable()

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

    def visit_Num(self, node):
        if type(node.n) is int:
            return LLVMConstant(types.Int(LLVMTypeEngine), node.n)
        elif type(node.n) is float:
            return LLVMConstant(types.Float(LLVMTypeEngine), node.n)

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
        realty = ty(LLVMTypeEngine)
        if name in self.symbols:
            raise VariableRedeclarationError(name)
        
        self.symbols[name] = LLVMVariable(name, realty, self.builder)

    def new_basic_block(self, name='uname'):
        self.__blockcounter += 1
        return self.function.append_basic_block('%s_%d'%(name, self.__blockcounter))

    def is_properly_close_basicblock(self):
        '''Check the last instruction of the current basic block.
        '''
        bb = self.builder.basic_block
        closing_inst_set = set(['ret', 'br', 'cbranch', 'unreachable'])
        if len(bb.instructions)==0: return False
        lastinst = bb.instructions[-1]
        if lastinst.opcode_name not in closing_inst_set:
            return False
        return True

