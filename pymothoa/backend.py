import logging
import ast

import types, dialect

from pymothoa.util.descriptor import Descriptor, instanceof
from compiler_errors import *

logger = logging.getLogger(__name__)

class CodeGenerationBase(ast.NodeVisitor):

    symbols = Descriptor(constant=True, constrains=instanceof(dict))
    __nodes = Descriptor(constant=True)

    def __init__(self, globalsymbols):
        '''
        globalsymbols -- A dict containing global symbols for the function.
        '''
        self.symbols = globalsymbols.copy()
        self.__nodes = []

    @property
    def current_node(self):
        return self.__nodes[-1]

    def visit(self, node):
        try:
            fn = getattr(self, 'visit_%s' % type(node).__name__)
        except AttributeError as e:
            logger.exception(e)
            logger.error('Unhandled visit to %s', ast.dump(node))
            raise InternalError(node)
        else:
            try:
                self.__nodes.append(node) # push current node
                return fn(node)
            except TypeError as e:
                logger.exception(e)
                raise InternalError(node, str(e))
            except (NotImplementedError, AssertionError) as e:
                logger.exception(e)
                raise InternalError(node, str(e))
            finally:
                self.__nodes.pop() # pop current node

    def visit_FunctionDef(self, node):
        # function def
        with self.generate_function(node.name) as fndef:
            # arguments
            self.visit(node.args)
            # function body
            for stmt in node.body:
                self.visit(stmt)
        # close function


    def visit_arguments(self, node):
        if node.vararg or node.kwarg or node.defaults:
            raise FunctionDeclarationError('Does not support variable/keyword/default arguments.')

        arguments=[]
        for arg in node.args:
            if not isinstance(arg.ctx, ast.Param):
                raise InternalError('Argument is not ast.Param?')
            name = arg.id
            arguments.append(name)

        if len(set(arguments)) != len(arguments):
            raise InternalError(node, '''Argument redeclared.
This error should have been caught by the Python parser.''')

        self.generate_function_arguments(arguments)

    def generate_function(self, name):
        raise NotImplementedError


    def generate_function_arguments(self, arguments):
        raise NotImplementedError

    def visit_Pass(self, node):
        pass

    def visit_Call(self, node):
        fn = self.visit(node.func)

        if type(fn) is type and issubclass(fn, dialect.Construct):
            # Special construct for our dialect
            try:
                handler = {
                    dialect.var: self.construct_var,
                }[fn]
            except KeyError:
                raise NotImplementedError(
                        'This construct has yet to be implemented.'
                        )
            else:
                return handler(fn, node)
        else:# is a real function call
            if node.keywords or node.starargs or node.kwargs:
                raise InvalidCall(node, 'Cannot use keyword or star arguments.')

            args = map(self.visit, node.args)
            return self.generate_call(fn, args) # return value

        raise InternalError(self.current_node, 'Unreachable')

    def generate_declare(self,  name, ty):
        raise NotImplementedError

    def construct_var(self, fn, node):
        if fn is not dialect.var:
            raise AssertionError('Implementation error.')

        if node.args:
            raise InvalidUseOfConstruct(
                    node,
                    ('Construct "var" must contain at least one'
                    ' keyword arguments in the form of "var ( name=type )".'),
                  )

        # for each defined variable
        for kw in node.keywords:
            #ty = self.visit(kw.value) # type
            ty = self.extract_type(kw.value)
            name = kw.arg             # name
            if name in self.symbols:
                raise VariableRedeclarationError(kw.value)
            variable = self.generate_declare(name, ty)
            # store new variable to symbol table
            self.symbols[name] = variable
        return # return None

    def extract_type(self, node):
        if isinstance(node, ast.Name): # simple symbols
            if not isinstance(node.ctx, ast.Load):
                raise InternalError(node, 'Only load context is possible.')
            return self.symbols[node.id]
        elif isinstance(node, ast.Call): # complex type
            fn = self.visit(node.func)
            if not issubclass(fn, types.DummyType):
                raise AssertionError('Not a dummy type.')
            if fn is types.Vector:
                # Defining a vector type
                if len(node.args) != 2:
                    raise InvalidUseOfConstruct(
                            node,
                            ('Vector constructor takes two arguments.\n'
                             'Hint: Vector(ElemType, ElemCount)')
                          )

                if node.keywords or node.starargs or node.kwargs:
                    raise InvalidUseOfConstruct(
                                node,
                                'Cannot use keyword or star arguments.'
                            )

                elemty = self.visit(node.args[0])
                elemct = self.constant_number(node.args[1])

                if type(elemty) is not type or not issubclass(elemty, types.Type):
                    raise InvalidUseOfConstruct(
                                node,
                                'Expecting a type for element type of vector.'
                          )

                if elemct <= 0:
                    raise InvalidUseOfConstruct(
                              node,
                              'Vector type must have at least one element.'
                          )


                newclsname = '__CustomVector__%s%d'%(elemty.__name__, elemct)
                newcls = type(newclsname, (types.GenericVector,), {
                    # List all class members of the new vector type.
                    'elemtype' : elemty,
                    'elemcount': elemct,
                })

                return newcls # return the new vector type class object
            elif fn is types.Array:
                # Defining an Array type
                if len(node.args) != 2:
                    raise InvalidUseOfConstruct(
                            node,
                            ('Array constructor takes two arguments.\n'
                             'Hint: Array(ElemType, ElemCount)')
                          )

                if node.keywords or node.starargs or node.kwargs:
                    raise InvalidUseOfConstruct(
                                node,
                                'Cannot use keyword or star arguments.'
                            )

                elemty = self.visit(node.args[0])
                elemct = self.visit(node.args[1]) # accept constants & variables

                if type(elemty) is not type or not issubclass(elemty, types.Type):
                    raise InvalidUseOfConstruct(
                                node,
                                'Expecting a type for element type of array.'
                          )

                if elemct <= 0:
                    raise InvalidUseOfConstruct(
                              node,
                              'array type must have at least one element.'
                          )

                newclsname = '__CustomArray__%s%s'%(elemty.__name__, elemct)
                newcls = type(newclsname, (types.GenericBoundedArray,), {
                    # List all class members of the new array type.
                    'elemtype' : elemty,
                    'elemcount': elemct,
                })

                return newcls # return the new array type class object

        raise InternalError(node, 'Cannot resolve type.')

    def visit_Expr(self, node):
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            value = self.visit(node.value)
            return getattr(value, node.attr)
        else:
            raise NotImplementedError('Storing into attribute is not supported.')

    def visit_Compare(self, node):
        if len(node.ops)!=1:
            raise NotImplementedError('Multiple operators in ast.Compare')

        if len(node.comparators)!=1:
            raise NotImplementedError('Multiple comparators in ast.Compare')

        lhs = self.visit(node.left)
        rhs = self.visit(node.comparators[0])
        op  = type(node.ops[0])
        return self.generate_compare(op, lhs, rhs)

    def visit_Return(self, node):
        value = self.visit(node.value)
        self.generate_return(value)

    def generate_return(self, value):
        raise NotImplementedError

    def generate_compare(self, op_class, lhs, rhs):
        raise NotImplementedError

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        op = type(node.op)
        return self.generate_binop(op, lhs, rhs)

    def generate_binop(self, op_class, lhs, rhs):
        raise NotImplementedError

    def visit_Assign(self, node):
        if len(node.targets)!=1:
            raise NotImplementedError('Mutliple targets in assignment.')
        target = self.visit(node.targets[0])
        value = self.visit(node.value)
        return self.generate_assign(value, target)

    def generate_assign(self, from_value, to_target):
        raise NotImplementedError

    def constant_number(self, node):
        if isinstance(node, ast.Num):
            retval = node.n
        else:
            if not isinstance(node, ast.Name):
                raise NotImplementedError
            if not isinstance(node.ctx, ast.Load):
                raise NotImplementedError

            retval = self.symbols[node.id]
        if ( not isinstance(retval, int)
             and not isinstance(retval, long)
             and not isinstance(retval, float) ):
            raise TypeError('Not a numeric constant.')
        return retval

    def visit_Num(self, node):
        if type(node.n) is int:
            return self.generate_constant_int(node.n)
        elif type(node.n) is float:
            return self.generate_constant_real(node.n)

    def generate_constant_int(self, val):
        raise NotImplementedError

    def generate_constant_real(self, val):
        raise NotImplementedError

    def visit_Subscript(self, node):
        assert isinstance(node.slice, ast.Index)
        ptr = self.visit(node.value)
        idx = self.visit(node.slice.value)
        if isinstance(ptr.type, types.GenericVector):
            # Access vector element
            if isinstance(node.ctx, ast.Load): # load
                return self.generate_vector_load_elem(ptr, idx)
            elif isinstance(node.ctx, ast.Store): # store
                return self.generate_vector_store_elem(ptr, idx)
        elif isinstance(ptr.type, types.GenericUnboundedArray):
            # Access array element
            if isinstance(node.ctx, ast.Load): # load
                return self.generate_array_load_elem(ptr, idx)
            elif isinstance(node.ctx, ast.Store): # store
                return self.generate_array_store_elem(ptr, idx)
        else: # Unsupported types
            raise InvalidSubscriptError(node)


    def generate_vector_load_elem(self, ptr, idx):
        raise NotImplementedError

    def generate_vector_store_elem(self, ptr, idx):
        raise NotImplementedError

    def generate_array_load_elem(self, ptr, idx):
        raise NotImplementedError

    def generate_array_store_elem(self, ptr, idx):
        raise NotImplementedError

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load): # load
            try: # lookup in the symbol table
                val = self.symbols[node.id]
            except KeyError: # does not exist
                raise UndefinedSymbolError(node)
            else: # load from stack
                if isinstance(val, int) or isinstance(val, long):
                    return self.generate_constant_int(val)
                elif isinstance(val, float):
                    return self.generate_constant_real(val)
                else:
                    return val
        elif isinstance(node.ctx, ast.Store): # store
            try:
                return self.symbols[node.id]
            except KeyError:
                raise UndefinedSymbolError(node)
        # unreachable
        raise AssertionError('unreachable')

    def visit_If(self, node):
        test = self.visit(node.test)
        iftrue_body = node.body
        orelse_body = node.orelse
        if len(orelse_body) not in [0,1]: raise AssertionError
        self.generate_if(test, iftrue_body, orelse_body)

    def visit_For(self, node):
        if node.orelse:
            raise NotImplementedError('Else in for-loop is not implemented.')
        iternode = node.iter

        str_only_support_forrange = 'Only for-range|for-xrange are supported.'
        if not isinstance(iternode, ast.Call):
            raise InvalidUseOfConstruct(str_only_support_forrange)

        looptype = iternode.func.id
        if looptype not in ['range', 'xrange']:
            raise InvalidUseOfConstruct(str_only_support_forrange)

        # counter variable
        counter_name = node.target.id
        if counter_name in self.symbols:
            raise VariableRedeclarationError(node.target)

        counter_ptr = self.generate_declare(node.target.id, types.Int)
        self.symbols[counter_name] = counter_ptr

        # range information
        iternode_arg_N = len(iternode.args)
        if iternode_arg_N==1: # only END is given
            zero = self.generate_constant_int(0)
            initcount = zero # init count is implicitly zero
            endcountpos = 0
        elif iternode_arg_N==2: # both BEGIN and END are given
            initcount = self.visit(iternode.args[0]) # init count is given
            endcountpos = 1
        else:
            raise NotImplementedError('Range(BEGIN, END, STEP) is not implemented')

        endcount = self.visit(iternode.args[endcountpos]) # end count

        loopbody = node.body
        self.generate_for_range(counter_ptr, initcount, endcount, loopbody)

    def visit_BoolOp(self, node):
        if len(node.values)!=2: raise AssertionError
        return self.generate_boolop(node.op, node.values[0], node.values[1])

    def generate_boolop(self, op_class, lhs, rhs):
        raise NotImplementedError

