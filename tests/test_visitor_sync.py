import importlib
import inspect
import re

from codefab.ast_nodes import Expr, Stmt
from codefab.visitor import Visitor


def _to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _all_concrete_subclasses(base: type) -> set[type]:
    for module_name in ("codefab.ast_nodes", "codefab.array_nodes"):
        importlib.import_module(module_name)

    found: set[type] = set()
    stack = list(base.__subclasses__())
    while stack:
        cls = stack.pop()
        if not inspect.isabstract(cls):
            found.add(cls)
        stack.extend(cls.__subclasses__())
    return found


def test_모든_Expr_Stmt_노드는_Visitor에_대응_메서드가_있다():
    nodes = _all_concrete_subclasses(Expr) | _all_concrete_subclasses(Stmt)

    missing = [
        (cls.__name__, f"visit_{_to_snake(cls.__name__)}")
        for cls in nodes
        if f"visit_{_to_snake(cls.__name__)}" not in Visitor.__abstractmethods__
    ]

    assert not missing, f"Visitor에 누락된 메서드: {missing}"


def test_Visitor의_모든_메서드는_실제_Element에_대응된다():
    nodes = _all_concrete_subclasses(Expr) | _all_concrete_subclasses(Stmt)
    node_visit_names = {f"visit_{_to_snake(cls.__name__)}" for cls in nodes}

    extra = Visitor.__abstractmethods__ - node_visit_names

    assert not extra, f"대응하는 Element가 없는 Visitor 메서드: {extra}"
