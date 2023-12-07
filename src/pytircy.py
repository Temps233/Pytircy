from ast import (
    AST,
    AnnAssign,
    Assign,
    BinOp,
    Call,
    Compare,
    Constant,
    FunctionDef,
    Import,
    Module,
    Name,
    NodeVisitor,
    Expr,
    Add,
    Return,
    Sub,
    Mult,
    Div,
    Mod,
    Attribute,
    If,
    Eq,
    NotEq,
    GtE,
    Gt,
    LtE,
    Lt,
    List,
    Subscript
)

class CompTimeCtx:
    def __init__(self):
        self.names = []

class Compiler(NodeVisitor):
    def __init__(self):
        super().__init__()
        self.ctx = CompTimeCtx()
    
    def generic_visit(self, node: AST):
        if (isinstance(node, list)):
            ret = ""
            for n in node:
                x = self.visit(n)
                ret += (x if x[-1] != '$' else x[:-1]) + ('\n' if x[-1] == '$' else ';\n')
            return ret
        raise NotImplementedError(type(node).__name__)

    def visit_Module(self, node: Module):
        return self.visit(node.body)
    
    def visit_Expr(self, node: Expr):
        return self.visit(node.value)
    
    def visit_Constant(self, node: Constant):
        if type(node.value) == str:
            if node.kind == 'u':
                if len(node.value) > 1:
                    raise ValueError("multi-char in char type")
                return f"'{node.value}'"
            if node.value.startswith("$cpp "):
                return node.value[5:]
            return f'"{node.value}"'
        
        elif type(node.value) == int:
            return str(node.value)
        
        elif type(node.value) == float:
            return str(node.value)
        
        elif type(node.value) == bool:
            return str(node.value).lower()
        
        else:
            raise TypeError("not supported constant type")
    
    def visit_BinOp(self, node: BinOp):
        if type(node.op) == Add:
            return f'({self.visit(node.left)} + {self.visit(node.right)})'
        
        if type(node.op) == Sub:
            return f'({self.visit(node.left)} - {self.visit(node.right)})'
        
        if type(node.op) == Mult:
            return f'({self.visit(node.left)} * {self.visit(node.right)})'
        
        if type(node.op) == Div:
            return f'({self.visit(node.left)} / {self.visit(node.right)})'
        
        if type(node.op) == Mod:
            return f'({self.visit(node.left)} % {self.visit(node.right)})'

        else:
            raise TypeError("not supported operator")        

    def visit_Name(self, node: Name):
        return node.id
    
    def visit_AnnAssign(self, node: AnnAssign):
        if type(node.annotation) != Name:
            raise TypeError("invalid type")
        if type(node.target) not in (Name, Subscript):
            raise SyntaxError("invalid target")
        result = f"{self.visit(node.annotation)} {self.visit(node.target)}"
        self.ctx.names.append(result.split()[1])
        if node.value is not None:
            result += f" = {self.visit(node.value)}"
        return result
    
    def visit_Assign(self, node: Assign):
        for tg in node.targets:
            if isinstance(tg, Name):
                if tg.id not in self.ctx.names:
                    raise NameError("undefined variable")
            elif isinstance(tg, Attribute):
                if tg.value not in self.ctx.names:
                    raise NameError("undefined variable")
        return f"{' = '.join(map(lambda x: self.visit(x), node.targets))} = {self.visit(node.value)}"

    def visit_Call(self, node: Call):
        return f"{self.visit(node.func)}({', '.join(map(lambda x: self.visit(x), node.args))})"
    
    def visit_If(self, node: If):
        if_clause = f"if ({self.visit(node.test)}) {{\n{self.visit(node.body)}}} "
        else_clause = f"else {{\n{self.visit(node.orelse)}}}$"
        return if_clause + else_clause
    
    def visit_Compare(self, node: Compare):
        if len(node.ops) != 1:
            raise SyntaxError("multi-comparison is not supported")
        op = node.ops[0]
        if type(op) == Eq:
            return f"({self.visit(node.left)} == {self.visit(node.comparators[0])})"
        elif type(op) == NotEq:
            return f"({self.visit(node.left)} != {self.visit(node.comparators[0])})"
        elif type(op) == GtE:
            return f"({self.visit(node.left)} >= {self.visit(node.comparators[0])})"
        elif type(op) == Gt:
            return f"({self.visit(node.left)} > {self.visit(node.comparators[0])})"
        elif type(op) == LtE:
            return f"({self.visit(node.left)} <= {self.visit(node.comparators[0])})"
        elif type(op) == Lt:
            return f"({self.visit(node.left)} < {self.visit(node.comparators[0])})"
    
    def visit_FunctionDef(self, node: FunctionDef):
        for arg in node.args.args:
            if arg.annotation is None:
                raise TypeError("argument type not specified")
        if node.returns is None:
            raise TypeError("return type not specified")
        if not isinstance(node.returns, Name):
            raise TypeError("invalid return type")
        func_head = f"{self.visit(node.returns)} {node.name}({', '.join(map(lambda x: f'{self.visit(x.annotation)} {x.arg}', node.args.args))})"
        return func_head + f" {{\n{self.visit(node.body)}}}$"
    
    def visit_Return(self, node: Return):
        return f'return {self.visit(node.value)}'

    def visit_Import(self, node: Import):
        if len(node.names) > 1:
            raise SyntaxError("multi-import is not supported")
        if node.names[0].asname:
            raise SyntaxError("import as is not supported")
        return f'#include <{node.names[0].name}>$'

    def visit_List(self, node: List):
        return f'{{{", ".join(map(lambda x: self.visit(x), node.elts))}}}'

    def visit_Subscript(self, node: Subscript):
        if not isinstance(node.slice, Constant) or not isinstance(node.slice.value, int):
            raise TypeError("Subscript can only contain integers")
        return f'{self.visit(node.value)}[{self.visit(node.slice)}]'