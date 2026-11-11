"""极小极大搜索与 Alpha-Beta 剪枝。

树的约定与实验要求一致：
- 根节点是 MAX 玩家，往下逐层交替；
- 非叶子节点用 children 表示子节点，叶子节点用 value 表示得分；
- 子节点按从左到右的顺序评估。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class Stats:
    nodes: int = 0            # 访问到的节点数（含根）
    leaves: int = 0           # 实际评估的叶节点数
    prunes: int = 0           # 被剪掉的子树个数

    def as_dict(self) -> Dict[str, int]:
        return {"nodes": self.nodes, "leaves": self.leaves, "prunes": self.prunes}


class TreeNode:
    """游戏树节点。叶子节点只有 value，内部节点只有 children。"""

    def __init__(self, value: Optional[float] = None, children: Optional[Sequence["TreeNode"]] = None):
        self.value = value
        self.children: List["TreeNode"] = list(children) if children else []

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def __repr__(self) -> str:  # 方便调试
        if self.is_leaf:
            return f"Leaf({self.value})"
        return f"Node({len(self.children)} children)"


def node_from_dict(data: Dict[str, Any]) -> TreeNode:
    """把题目给的 JSON 结构转换成 TreeNode 树。"""
    if "children" in data and data["children"]:
        return TreeNode(children=[node_from_dict(c) for c in data["children"]])
    return TreeNode(value=data.get("value"))


def build_demo_tree() -> TreeNode:
    """题目三的示例树：叶子 3 5 6 9 1 2，根为 MAX。"""
    leaves = [TreeNode(value=v) for v in (3, 5, 6, 9, 1, 2)]
    max1 = TreeNode(children=leaves[0:2])
    max2 = TreeNode(children=leaves[2:4])
    max3 = TreeNode(children=leaves[4:6])
    min1 = TreeNode(children=[max1, max2])
    min2 = TreeNode(children=[max2, max3])
    return TreeNode(children=[min1, min2])


def minimax(root: TreeNode, stats: Optional[Stats] = None) -> float:
    """不带剪枝的极小极大，返回根节点的最优值。"""
    stats = stats if stats is not None else Stats()

    def rec(node: TreeNode, is_max: bool) -> float:
        stats.nodes += 1
        if node.is_leaf:
            stats.leaves += 1
            return float(node.value)
        values = [rec(child, not is_max) for child in node.children]
        return max(values) if is_max else min(values)

    return rec(root, True)


def alpha_beta(root: TreeNode, stats: Optional[Stats] = None) -> float:
    """Alpha-Beta 剪枝版本，返回根节点的最优值（应与 minimax 相同）。"""
    stats = stats if stats is not None else Stats()

    def rec(node: TreeNode, alpha: float, beta: float, is_max: bool) -> float:
        stats.nodes += 1
        if node.is_leaf:
            stats.leaves += 1
            return float(node.value)

        if is_max:
            value = -math.inf
            for child in node.children:
                value = max(value, rec(child, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    stats.prunes += 1
                    break
            return value

        value = math.inf
        for child in node.children:
            value = min(value, rec(child, alpha, beta, True))
            beta = min(beta, value)
            if alpha >= beta:
                stats.prunes += 1
                break
        return value

    return rec(root, -math.inf, math.inf, True)


def alpha_beta_verbose(root: TreeNode) -> Dict[str, Any]:
    """返回根节点每个子节点的取值，用来观察剪枝发生在哪一层。"""
    detail = []
    alpha, beta = -math.inf, math.inf
    for i, child in enumerate(root.children):
        value = _ab(child, alpha, beta, False, Stats())
        detail.append({"child": i, "value": value})
        alpha = max(alpha, value)
    return {"children": detail}


def _ab(node: TreeNode, alpha: float, beta: float, is_max: bool, stats: Stats) -> float:
    if node.is_leaf:
        return float(node.value)
    if is_max:
        value = -math.inf
        for child in node.children:
            value = max(value, _ab(child, alpha, beta, False, stats))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    value = math.inf
    for child in node.children:
        value = min(value, _ab(child, alpha, beta, True, stats))
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def reversed_children(root: TreeNode) -> TreeNode:
    """按“从右到左”的顺序访问子节点，用于比较访问顺序对剪枝的影响。"""
    return TreeNode(
        value=root.value,
        children=[reversed_children(c) for c in reversed(root.children)] if root.children else None,
    )
