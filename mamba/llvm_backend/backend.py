import ast

from pyon.descriptor import Descriptor, instanceof

from mamba import dialect
from mamba.compiler_errors import *

from types import *
from values import *
import llvm # binding

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
                    raise MissingReturnError(node)

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
        from function import LLVMFunction
        fn = self.visit(node.func)

        if type(fn) is type and issubclass(fn, dialect.Construct):
            if issubclass(fn, dialect.var):
                assert not node.args
                for kw in node.keywords:
                    ty = self.visit(kw.value)
                    name = kw.arg
                    try:
                        self.declare(name, ty)
                    except KeyError:
                        raise VariableRedeclarationError(kw.value)
                return
            else:
                assert False
        elif fn is types.Vector:
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            ty = self.visit(node.args[0])
            ct = self.get_constant(node.args[1])

            newclsname = '__CustomVector__%s%d'%(ty.__name__, ct)
            newcls = type(newclsname, (types.GenericVector,), {
                'elemtype': ty,
                'elemcount': ct,
            })
            return newcls
        elif isinstance(fn, LLVMFunction):
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            return self.call_function(fn.code_llvm, args, fn.retty, fn.argtys)
        elif fn is self.function:
            assert not node.keywords
            assert not node.starargs
            assert not node.kwargs
            args = map(self.visit, node.args)
            return self.call_function(fn, args, self.retty, self.argtys)

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
                raise UndefinedSymbolError(node)
            else: # load from stack
                if type(val) is int:
                    return LLVMConstant(LLVMType(types.Int), val)
                elif type(val) is float:
                    return LLVMConstant(LLVMType(types.Double), val)
                else:
                    return val
        else:
            assert isinstance(node.ctx, ast.Store)
            try:
                return self.symbols[node.id]
            except KeyError:
                raise UndefinedSymbolError(node)

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

        try:
            counter_ptr = self.declare(node.target.id, types.Int)
        except KeyError:
            raise VariableRedeclarationError(node.target)

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
        if isinstance(ptr.type, LLVMVector):
            if isinstance(node.ctx, ast.Load):
                elemval = self.builder.extract_element(ptr.value(self.builder), idx.value(self.builder))
                return LLVMTempValue(elemval, ptr.type.elemtype)
            else:
                assert isinstance(node.ctx, ast.Store)
                zero = LLVMConstant(LLVMType(types.Int), 0)
                indices = map(lambda X: X.value(self.builder), [zero, idx])
                addr = self.builder.gep2(ptr.pointer, indices)
                return LLVMTempPointer(addr, ptr.type.elemtype)
                #elemval = self.builder.insert_element(ptr.value(self.builder)
        else:
            assert isinstance(ptr.type, LLVMUnboundedArray)
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
            raise KeyError(name)

        self.symbols[name] = var = LLVMVariable(name, realty, self.builder)
        return var

    def call_function(self, fn, args, retty, argtys):
        arg_values = map(lambda X: LLVMTempValue(X.value(self.builder), X.type), args)
        # cast types
        for i, argty in enumerate(argtys):
            arg_values[i] = argty.cast(arg_values[i], self.builder)

        out = self.builder.call(fn, arg_values)
        return LLVMTempValue(out, retty)

    def new_basic_block(self, name='uname'):
        self.__blockcounter += 1
        return self.function.append_basic_block('%s_%d'%(name, self.__blockcounter))

    def get_constant(self, node):
        if isinstance(node, ast.Num):
            return node.n
        else:
            if not isinstance(node, ast.Name):
                raise NotImplementedError
            if not isinstance(node.ctx, ast.Load):
                raise NotImplementedError
            return self.symbols[node.id]

