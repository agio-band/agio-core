import re
import math
import operator
import random
from typing import Callable, Dict, List, Optional


class ExpressionSolver:
    """
    Expression solver class
    - any variable must start with "$"
    - you need to provide function for getting the variables
    - variable can contain dots and underscores
    """
    FUNCTIONS: Dict[str, Callable] = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "abs": abs, "pow": pow,
        "random": random.random, "randint": random.randint,
        "int": int, "float": float,
    }
    OPERATORS = {
        '==': (1, operator.eq), '!=': (1, operator.ne),
        '<': (1, operator.lt), '<=': (1, operator.le),
        '>': (1, operator.gt), '>=': (1, operator.ge),
        '+': (2, operator.add), '-': (2, operator.sub),
        '*': (3, operator.mul), '/': (3, operator.truediv),
        '//': (3, operator.floordiv), '%': (3, operator.mod),
        '**': (4, operator.pow),
    }

    def __init__(self, eval_variable_callback: Callable[[str], float]):
        self.eval_var = eval_variable_callback
        self._tokens: List[str] = []
        self._pos: int = 0

    def solve(self, expression: str) -> float:
        self._tokens = self._tokenize(expression)
        self._pos = 0
        if not self._tokens:
            return 0.0
        return self._parse_expression()

    def _tokenize(self, expr: str) -> List[str]:
        # 2-chars operators
        # variables
        # digits
        # funcs
        # 1-char operators
        pattern = re.compile(r'''
            \*\*                   |  
            \$[a-zA-Z0-9_.]+       |
            [0-9]*\.?[0-9]+        |
            [a-zA-Z_][a-zA-Z0-9_]* |
            [+\-*/(),<>%]
            ''',
        re.VERBOSE)
        return [t for t in pattern.findall(expr) if t.strip()]

    def _peek(self) -> Optional[str]:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self, expected: Optional[str] = None) -> str:
        token = self._tokens[self._pos]
        if expected and token != expected:
            raise SyntaxError(f"Expected {expected}, got {token}")
        self._pos += 1
        return token

    def _parse_expression(self) -> float:
        return self._parse_binary(0)

    def _parse_binary(self, min_precedence: int) -> float:
        left = self._parse_primary()
        while True:
            token = self._peek()
            if not token or token not in self.OPERATORS:
                break

            prec, op_func = self.OPERATORS[token]
            if prec < min_precedence:
                break

            self._consume()
            next_min_prec = prec if token == '**' else prec + 1
            right = self._parse_binary(next_min_prec)

            left = op_func(left, right)
            if isinstance(left, bool):
                left = float(left)
        return left

    def _parse_primary(self) -> float:
        token = self._consume()

        if token == '(':
            result = self._parse_expression()
            self._consume(')')
            return result

        if token == '-':
            return -self._parse_primary()

        if token.startswith('$'):
            return self.eval_var(token[1:])

        if token in self.FUNCTIONS:
            if self._peek() == '(':
                self._consume('(')
                args = []
                if self._peek() != ')':
                    while True:
                        args.append(self._parse_expression())
                        if self._peek() == ',':
                            self._consume(',')
                            continue
                        break
                self._consume(')')
                return self.FUNCTIONS[token](*args)
            return self.FUNCTIONS[token]()

        try:
            return float(token)
        except ValueError:
            raise ValueError(f"Unknown token: {token}")
