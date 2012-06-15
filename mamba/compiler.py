import logging
import ast, inspect

import types

logger = logging.getLogger(__name__)

def function(ret=types.Void, args=[]):
    def wrapper(func):
        assert type(func).__name__=='function', (
                '"%s" is not a function.'%func.__name__
        )

        llvmfn = LLVMFunction(func, ret, args)
        llvmfn.compile()
        llvmfn.optimize()
        return llvmfn

    return wrapper

# ---------------------------------------------

class LLVMModuleManager(object):
    from pyon.descriptor import Descriptor

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

class LLVMFunction(object):
    from pyon.descriptor import Descriptor

    retty = Descriptor(constant=True)
    argtys = Descriptor(constant=True)

    code_python = Descriptor(constant=True)
    code_llvm = Descriptor(constant=True)

    manager = LLVMModuleManager() # class member

    def __init__(self, orig_func, retty, argtys):
        self.code_python = orig_func
        self.retty = retty
        self.argtys = argtys

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
        tyadaptor = types.TypeAdaptor('llvm')
        args = [tyadaptor.send(self.argtys[i], arg)
                for i, arg in enumerate(args)]

        retval = self.manager.executor.run_function(self.code_llvm, args)
        return tyadaptor.recv(self.retty, retval)

# ---------------------------------------------

class CompilerError(Exception):
    pass

class VariableRedeclarationError(CompilerError):
    pass

class UndefinedSymbolError(CompilerError):
    pass

class MissingReturnError(CompilerError):
    pass


from llvm.core import *
class LLVMCodeGenerator(ast.NodeVisitor):
    from pyon.descriptor import Descriptor, instanceof

    module        = Descriptor(constant=True)
    retty         = Descriptor(constant=True)
    retty_raw     = Descriptor(constant=True)
    argtys        = Descriptor(constant=True)
    argtys_raw    = Descriptor(constant=True)
    type_factory  = Descriptor(constant=True)
    function      = Descriptor(constant=True)
    symbols       = Descriptor(constant=True, constrains=instanceof(dict))
    typeinfo      = Descriptor(constant=True, constrains=instanceof(dict))
    

    def __init__(self, module, retty, argtys, symbols):
        super(LLVMCodeGenerator, self).__init__()
        self.module = module
        self.type_factory = types.TypeAdaptor('llvm')
        self.retty = self.type_factory.make(retty)
        self.retty_raw = retty
        self.argtys = map(self.type_factory.make, argtys)
        self.argtys_raw = argtys
        # symbol table
        self.symbols = symbols.copy()
        # typeinfo table
        self.typeinfo = {}

    def visit_FunctionDef(self, node):
        fnty = Type.function(self.retty, self.argtys)
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
            #self.function.args[i].name = name+'.arg'
            ptr = self.builder.alloca(self.argtys[i])
            self.builder.store(self.function.args[i], ptr)
            self.symbols[name] = ptr
            self.typeinfo[ptr.value_id] = self.argtys_raw[i]

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
            out = self.builder.call(fn.code_llvm, args)
            self.typeinfo[out.value_id] = fn.retty
            return out
        elif fn is self.function:
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            out = self.builder.call(fn, args)
            self.typeinfo[out.value_id] = self.retty_raw
            return out

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
        fn = getattr(self, 'binop_%s'%type(node.ops[0]).__name__)
        return fn(lhs, rhs)

    def visit_Return(self, node):
        value = self.visit(node.value)
        value = self.cast(value, self.retty_raw)
        self.builder.ret(value)

    def visit_Assign(self, node):
        assert len(node.targets)==1, 'Not yet implemented multi target in assignment'
        target = self.visit(node.targets[0])
        value = self.visit(node.value)
        self.builder.store(value, target)

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = type(node.op)
        fn = getattr(self, 'binop_%s'%op.__name__)
        return fn(lhs, rhs)

    def visit_Num(self, node):
        assert type(node.n) is int
        out = Constant.int(self.type_factory.make(types.Int), node.n)
        self.typeinfo[out.value_id] = types.Int
        return out

    def visit(self, node):
        try:
            fn = getattr(self, 'visit_%s' % type(node).__name__)
        except AttributeError:
            logger.debug('Unhandled visit to %s', ast.dump(node))
            raise
            # return super(LLVMCodeGenerator, self).visit(node)
        else:
            return fn(node)

    def binop_Add(self, lhs, rhs):
        lhs, rhs = self.coerce(lhs, rhs)
        out = self.builder.add(lhs, rhs)
        self.copy_typeinfo(out, lhs)
        return out

    def binop_Sub(self, lhs, rhs):
        lhs, rhs = self.coerce(lhs, rhs)
        out = self.builder.sub(lhs, rhs)
        self.copy_typeinfo(out, lhs)
        return out

    def binop_Mult(self, lhs, rhs):
        lhs, rhs = self.coerce(lhs, rhs)
        out = self.builder.mul(lhs, rhs)
        self.copy_typeinfo(out, lhs)
        return out

    def binop_Div(self, lhs, rhs):
        lhs, rhs = self.coerce(lhs, rhs)
        out = self.builder.sdiv(lhs, rhs)
        self.copy_typeinfo(out, lhs)
        return out

    def binop_LtE(self, lhs, rhs):
        lhs, rhs = self.coerce(lhs, rhs)
        out = self.builder.icmp(ICMP_SLE, lhs, rhs)
        self.copy_typeinfo(out, lhs)
        return out

    def declare(self, name, ty):
        if type(ty) is type and issubclass(ty, types.Type):
            realty = self.type_factory.make(ty)
        else:
            raise TypeError(ty)

        if name in self.symbols:
            raise VariableRedeclarationError(name)

        ptr = self.builder.alloca(realty, name=name)
        self.symbols[name] = ptr
        self.typeinfo[ptr.value_id] = ty

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

    def coerce(self, lhs, rhs):
        lty = self.typeinfo[lhs.value_id]
        rty = self.typeinfo[rhs.value_id]
        if lty is rty:
            return lhs, rhs
        elif lty.rank > rty.rank:
            return lhs, self.cast(rhs, lty)
        else:
            return self.cast(lhs, rty), rhs

    def cast(self, val, ty):
        srcty = self.typeinfo[val.value_id]
        if ty is srcty: return val
        return self.type_factory.cast(ty, val, srcty, builder=self.builder)

    def copy_typeinfo(self, dst, src):
        try:
            self.typeinfo[dst.value_id] = self.typeinfo[src.value_id]
        except KeyError:
            print self.builder.basic_block
            raise
