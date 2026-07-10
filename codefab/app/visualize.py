"""토큰 스트림 / AST를 모던한 스타일의 Graphviz(DOT) 그래프로 만드는 헬퍼.

`st.graphviz_chart`는 DOT 소스 문자열을 그대로 받아 클라이언트에서 렌더링하므로,
여기서는 `graphviz` 파이썬 패키지 없이 DOT 텍스트만 직접 조립한다.
"""

import dataclasses
from collections import deque
from dataclasses import dataclass

from codefab.ast import Expr, MethodDecl, Stmt
from codefab.common.tokens import Token

_NAME_LIKE_FIELDS = ("name", "operator", "keyword")

# DOT 소스가 그대로 브라우저의 SVG font-family로 전달되므로 콤마로 구분된
# 폴백 목록을 쓸 수 있다 — Pretendard가 있으면 그걸, 없으면 시스템 한글 폰트로.
_FONT = "Pretendard, Segoe UI, Malgun Gothic, sans-serif"

# 노드 종류별 스타일: (채우기 색, 테두리 색, 글자 색) — claude.ai 톤의 웜 크림/테라코타 팔레트
_CATEGORY_STYLES = {
    "root": ("#3D3929", "#3D3929", "#F5F4EE"),
    "stmt": ("#F3DDD1", "#D97757", "#8A3B21"),
    "expr": ("#F5EAD0", "#C9A227", "#7A5C1E"),
    "method": ("#E3E8D9", "#7A9A6B", "#3F5233"),
    "token": ("#EDE9DC", "#B8AFA0", "#5C5648"),
}


@dataclass
class GraphNode:
    label_parts: list[str]
    category: str


def _category(node: object) -> str:
    if isinstance(node, Token):
        return "token"
    if isinstance(node, MethodDecl):
        return "method"
    if isinstance(node, Expr):
        return "expr"
    if isinstance(node, Stmt):
        return "stmt"
    return "root"


def label_parts(node: object) -> list[str]:
    """노드를 사람이 읽을 라벨의 줄(line) 목록으로 표현."""
    if isinstance(node, Token):
        return [node.type.name, repr(node.lexeme)]
    parts = [type(node).__name__]
    for field in _NAME_LIKE_FIELDS:
        value = getattr(node, field, None)
        if isinstance(value, Token):
            parts.append(value.lexeme)
    if type(node).__name__ == "Literal":
        parts.append(repr(node.value))
    return parts


def _child_edges(node: object) -> list[tuple[str, object]]:
    """(간선 라벨, 자식 노드) 목록. Expr/Stmt/Token/MethodDecl 및 이들의 list만 대상."""
    if isinstance(node, Token) or not dataclasses.is_dataclass(node):
        return []
    edges = []
    for field in dataclasses.fields(node):
        value = getattr(node, field.name)
        if isinstance(value, (Expr, Stmt, Token, MethodDecl)):
            edges.append((field.name, value))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, (Expr, Stmt, Token, MethodDecl)):
                    edges.append((f"{field.name}[{i}]", item))
    return edges


def build_ast_graph(
    statements: list[Stmt],
) -> tuple[list[GraphNode], list[tuple[int, int, str]]]:
    """루트("Program")에서 시작해 BFS 순서로 전체 AST를 노드/간선 목록으로 만든다."""
    nodes = [GraphNode(["Program"], "root")]
    edges: list[tuple[int, int, str]] = []
    queue: deque[tuple[int, str, object]] = deque(
        (0, f"[{i}]", stmt) for i, stmt in enumerate(statements)
    )

    while queue:
        parent_id, edge_label, node = queue.popleft()
        node_id = len(nodes)
        nodes.append(GraphNode(label_parts(node), _category(node)))
        edges.append((parent_id, node_id, edge_label))
        for child_label, child in _child_edges(node):
            queue.append((node_id, child_label, child))

    return nodes, edges


def build_token_graph(
    tokens: list[Token],
) -> tuple[list[GraphNode], list[tuple[int, int, str]]]:
    """토큰을 왼쪽에서 오른쪽으로 이어지는 체인으로 표현."""
    nodes = [GraphNode(label_parts(token), "token") for token in tokens]
    edges = [(i, i + 1, "") for i in range(len(tokens) - 1)]
    return nodes, edges


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _dot_label(node: GraphNode) -> str:
    return "\\n".join(_escape(part) for part in node.label_parts)


def _dot_node(node_id: int, node: GraphNode) -> str:
    fill, border, font = _CATEGORY_STYLES[node.category]
    return (
        f'  n{node_id} [label="{_dot_label(node)}", fillcolor="{fill}", '
        f'color="{border}", fontcolor="{font}"];'
    )


def render_ast_dot(nodes: list[GraphNode], edges: list[tuple[int, int, str]]) -> str:
    """모던한 스타일의 완성된 AST DOT 소스를 만든다 (애니메이션 없음, 최종 그래프만)."""
    lines = [
        "digraph AST {",
        '  bgcolor="transparent";',
        '  rankdir="TB";',
        "  nodesep=0.35;",
        "  ranksep=0.55;",
        f'  node [shape=box, style="rounded,filled", penwidth=1.4, fontname="{_FONT}", '
        'fontsize=12, margin="0.2,0.14"];',
        '  edge [color="#B8AFA0", arrowsize=0.7];',
    ]
    for node_id, node in enumerate(nodes):
        lines.append(_dot_node(node_id, node))
    for parent_id, child_id, _ in edges:
        # 필드 라벨은 일부러 안 그린다 — 자식이 그려지는 좌→우 순서 자체가 이미
        # dataclass 필드 선언 순서(예: left/operator/right)를 그대로 반영하기 때문에,
        # 라벨 없이도 구조가 읽힌다. graphviz의 xlabel 자동 배치는 트리가 빽빽해지면
        # 겹침을 완전히 막지 못해 라벨을 아예 없애는 편이 더 확실하다.
        lines.append(f"  n{parent_id} -> n{child_id};")
    lines.append("}")
    return "\n".join(lines)


def render_token_dot(nodes: list[GraphNode], edges: list[tuple[int, int, str]]) -> str:
    """모던한 스타일의 완성된 토큰 체인 DOT 소스를 만든다."""
    lines = [
        "digraph Tokens {",
        '  bgcolor="transparent";',
        '  rankdir="LR";',
        "  nodesep=0.3;",
        f'  node [shape=box, style="rounded,filled", penwidth=1.4, fontname="{_FONT}", '
        'fontsize=12, margin="0.2,0.12"];',
        '  edge [color="#B8AFA0", arrowsize=0.6];',
    ]
    for node_id, node in enumerate(nodes):
        lines.append(_dot_node(node_id, node))
    for parent_id, child_id, _ in edges:
        lines.append(f"  n{parent_id} -> n{child_id};")
    lines.append("}")
    return "\n".join(lines)
