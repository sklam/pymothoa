class CompilerError(Exception):
    message = 'Unspecified compiler error.'
    def __init__(self, node_or_error, additional=None):
        if isinstance(node_or_error, CompilerError):
            assert additional
            error = node_or_error
            super(CompilerError, self).__init__('\n'.join([additional, str(error)]))
            self.line = error.line
            self.col = error.col
        else:
            assert additional is None
            node = node_or_error
            super(CompilerError, self).__init__(self.message)
            self.line = node.lineno
            self.col = node.col_offset


class VariableRedeclarationError(CompilerError):
    message = 'Variable redeclared.'

class UndefinedSymbolError(CompilerError):
    message = '''Symbol has not been defined.
Hint: Mamba requires all variables to be defined using var ( Name = Type, ... ) construct prior to use.'''

class MissingReturnError(CompilerError):
    message = 'Function missing return statement.'

class InternalError(CompilerError):
    message = 'Internal error of the compiler. Can be unimplemented features.'
