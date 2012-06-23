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
                self.__nodes.append(node)
                return fn(node)
            except (NotImplementedError, AssertionError) as e:
                logger.exception(e)
                raise InternalError(node, str(e))
            finally:
                self.__nodes.pop()
                
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

    def define_function(self, name):
        raise NotImplementedError

    def visit_Pass(self, node):
        pass
