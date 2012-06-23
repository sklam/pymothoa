import logging
import ast
from contextlib import contextmanager

from pymothoa.util.descriptor import Descriptor, instanceof
from pymothoa import dialect
from pymothoa.compiler_errors import *
from pymothoa.backend import CodeGenerationBase

from types import *
from values import *

import llvm # binding

logger = logging.getLogger(__name__)

class LLVMCodeGenerator(CodeGenerationBase):
    jit_engine    = Descriptor(constant=True)
    retty         = Descriptor(constant=True)
    argtys        = Descriptor(constant=True)
    function      = Descriptor(constant=True)


    def __init__(self, jit_engine, retty, argtys, symbols):
        super(LLVMCodeGenerator, self).__init__(symbols)
        self.jit_engine = jit_engine
        self.retty = retty
        self.argtys = argtys

    @contextmanager
    def generate_function(self, name):
        retty = self.retty.type()
        argtys = map(lambda X: X.type(), self.argtys)

        namespace = self.symbols['__name__']
        realname = '.'.join([namespace,name])
        self.function = self.jit_engine.make_function(realname, retty, argtys)

        if not self.function.valid():
            raise FunctionDeclarationError(
                    self.current_node,
                    self.jit_engine.last_error()
                )

        self.symbols[name] = self.function

        if self.function.name() != realname:
            raise InternalError(self.current_node,
                    'Generated function has a different name: %s'%(
                    self.function.name() ) )

        # make basic block
        bb_entry = self.function.append_basic_block("entry")
        self.__blockcounter = 0

        # make instruction builder
        self.builder = llvm.Builder()
        self.builder.insert_at(bb_entry)

        yield # wait until args & body are generated

        # close function
        if not self.builder.is_block_closed():
            if isinstance(self.retty, types.Void):
                # no return
                self.builder.ret_void()
            else:
                raise MissingReturnError(self.current_node)

    def generate_function_arguments(self, arguments):
        fn_args = self.function.arguments()
        for i, name in enumerate(arguments):
            var = LLVMVariable(name, self.argtys[i], self.builder)
            self.builder.store(fn_args[i], var.pointer)
            self.symbols[name] = var

    def generate_call(self, fn, args):
        from function import LLVMFunction
        if isinstance(fn, LLVMFunction): # another function
            retty = fn.retty
            argtys = fn.argtys
            fn = fn.code_llvm
        elif fn is self.function: # recursion
            retty = self.retty
            argtys = self.argtys
        else:
            raise InvalidCall(self.current_node)

        return self._call_function(fn, args, retty, argtys)

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

        counter_name = node.target.id
        if counter_name in self.symbols:
            raise VariableRedeclarationError(node.target)
        counter_ptr = self.generate_declare(node.target.id, types.Int)
        self.symbols[counter_name] = counter_ptr

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
        counter_next = self.builder.add(counter_ptr.value(self.builder),
                                        one.value(self.builder))
        self.builder.store(counter_next, counter_ptr.pointer)
        self.builder.branch(bb_cond)

        # exit
        self.builder.insert_at(bb_exit)

    def generate_assign(self, from_value, to_target):
        casted = to_target.type.cast(from_value, self.builder)
        self.builder.store(casted, to_target.pointer)
        return casted

    def generate_compare(self, op_class, lhs, rhs):
        ty = lhs.type.coerce(rhs.type)
        lval = ty.cast(lhs, self.builder)
        rval = ty.cast(rhs, self.builder)
        fn = getattr(ty, 'op_%s'%op_class.__name__.lower())
        return fn(lval, rval, self.builder)

    def generate_return(self, value):
        casted = self.retty.cast(value, self.builder)
        self.builder.ret(casted)

    def generate_binop(self, op_class, lhs, rhs):
        ty = lhs.type.coerce(rhs.type)
        lval = ty.cast(lhs, self.builder)
        rval = ty.cast(rhs, self.builder)

        fn = getattr(ty, 'op_%s'%op_class.__name__.lower())
        return LLVMTempValue(fn(lval, rval, self.builder), ty)


    def generate_constant_int(self, value):
        return LLVMConstant(LLVMType(types.Int), value)

    def generate_constant_real(self, value):
        return LLVMConstant(LLVMType(types.Double), value)

    def generate_declare(self, name, ty):
        realty = LLVMType(ty)
        return LLVMVariable(name, realty, self.builder)

    def _call_function(self, fn, args, retty, argtys):
        arg_values = map(lambda X: LLVMTempValue(X.value(self.builder), X.type), args)
        # cast types
        for i, argty in enumerate(argtys):
            arg_values[i] = argty.cast(arg_values[i], self.builder)

        out = self.builder.call(fn, arg_values)
        return LLVMTempValue(out, retty)

    def new_basic_block(self, name='uname'):
        self.__blockcounter += 1
        return self.function.append_basic_block('%s_%d'%(name, self.__blockcounter))

    def generate_vector_load_elem(self, ptr, idx):
        elemval = self.builder.extract_element(
                    ptr.value(self.builder),
                    idx.value(self.builder),
                  )
        return LLVMTempValue(elemval, ptr.type.elemtype)

    def generate_vector_store_elem(self, ptr, idx):
        zero = LLVMConstant(LLVMType(types.Int), 0)
        indices = map(lambda X: X.value(self.builder), [zero, idx])
        addr = self.builder.gep2(ptr.pointer, indices)
        return LLVMTempPointer(addr, ptr.type.elemtype)

    def generate_array_load_elem(self, ptr, idx):
        ptr_val = ptr.value(self.builder)
        idx_val = idx.value(self.builder)
        ptr_offset = self.builder.gep(ptr_val, idx_val)
        return LLVMTempValue(self.builder.load(ptr_offset), ptr.type.elemtype)

    def generate_array_store_elem(self, ptr, idx):
        ptr_val = ptr.value(self.builder)
        idx_val = idx.value(self.builder)
        ptr_offset = self.builder.gep(ptr_val, idx_val)
        return LLVMTempPointer(ptr_offset, ptr.type.elemtype)
