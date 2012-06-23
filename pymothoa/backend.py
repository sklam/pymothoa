import logging
import ast

import types, dialect
from compiler_errors import CompilerError, InternalError

logger = logging.getLogger(__name__)

class CodeGenerationBase(ast.NodeVisitor):

    __slots__ = '__nodes'

    def __init__(self):
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
            except (NotImplementedError, AssertionError) as e:
                logger.exception(e)
                raise InternalError(node, str(e))
            finally:
                self.__nodes.pop() # pop current node

    def visit_FunctionDef(self, node):
        # function def
        close = self.generate_function(node.name) # generate header
        # arguments
        self.visit(node.args)
        # function body
        for stmt in node.body:
            self.visit(stmt)
        else:
            close() # close function

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

        elif fn is types.Vector:
            # Defining a vector type
            if node.keywords or node.starargs or node.kwargs:
                raise InvalidUseOfConstruct(
                            node,
                            'Cannot use keyword or star arguments.'
                        )

            elemty = self.visit(node.args[0])
            elemct = self.get_constant(node.args[1])

            newclsname = '__CustomVector__%s%d'%(elemty.__name__, elemct)
            newcls = type(newclsname, (types.GenericVector,), {
                # List all class members of the new vector type.
                'elemtype' : elemty,
                'elemcount': elemct,
            })

            return newcls # return the new vector type class object

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
                    'Construct "var" must contain at least one keyword arguments in the form of "var ( name=type )".'
                )
        # For each defined variable
        for kw in node.keywords:
            ty = self.visit(kw.value) # type
            name = kw.arg             # name
            try:
                self.generate_declare(name, ty)
            except KeyError:
                raise VariableRedeclarationError(kw.value)
        return # return None
