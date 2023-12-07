from pytircy import Compiler
import click, ast

@click.option('--output', '-o', type=click.File('w'), default=None)
@click.argument('source', type=click.File('r'))
@click.command()
def compile(source, output):
    source = source.read()
    nodes = ast.parse(source)

    compiler = Compiler()
    out = compiler.visit(nodes)

    if output is None:
        with open('out.pytircy.cpp', 'w') as output:
            output.write(out)
    else:
        output.write(out)

print("Pytircy Compiler v1.0.1")
print("Copyright (c) 2023 Temps233")
compile()
