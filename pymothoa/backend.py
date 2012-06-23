import logging
import ast
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
        close = self.define_function(node.name) # generate header
        # arguments
        self.visit(node.args)
        # function body
        for stmt in node.body:
            self.visit(stmt)
        else:
            close() # close function

    def visit_arguments(self, node):
        assert not node.vararg, 'Variable argument not yet supported.'
        assert not node.kwarg, 'Does not support keyword argument'
        assert not node.defaults, 'Does not support default argument'

        arguments=[]
        for arg in node.args:
            if not isinstance(arg.ctx, ast.Param):
                raise InternalError('Argument is not ast.Param?')

            name = arg.id
            arguments.append(name)

        if len(set(arguments))!=len(arguments):
            raise InternalError(node, '''Argument redeclared.
This error should have been caught by the Python parser.''')

        self.define_function_arguments(arguments)

    def define_function(self, name):
        raise NotImplementedError


    def define_function_arguments(self, arguments):
        raise NotImplementedError

    def visit_Pass(self, node):
        pass
