import logging
import ast

logger = logging.getLogger(__name__)

class CodeGenerationBase(ast.NodeVisitor):
    def visit(self, node):
        try:
            fn = getattr(self, 'visit_%s' % type(node).__name__)
        except AttributeError as e:
            logger.exception(e)
            logger.error('Unhandled visit to %s', ast.dump(node))
            raise InternalError()
        else:
            try:
                return fn(node)
            except (NotImplementedError, AssertionError) as e:
                logger.exception(e)
                raise InternalError(node)
