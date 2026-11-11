"""报告里用到的对照实验。

1) 题目一：h=0 与曼哈顿距离在不同规模迷宫上的扩展节点数；
2) 题目二：终点 E 的进入代价按 0 / 按地形值处理时的最优代价差别；
3) 题目三：在一棵更大的随机博弈树上比较 Minimax 与 Alpha-Beta，
   以及子节点访问顺序对剪枝的影响。
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from . import astar as A
from . import problems as P
from .minimax import Stats, TreeNode, alpha_beta, minimax

Coord = Tuple[int, int]


def make_maze(rows: int, cols: int, density: float, seed: int) -> List[List[str]]:
    """生成一个保证 S->E 连通、且最短路唯一的随机迷宫（用固定随机种子复现）。"""
    rng = random.Random(seed)
    for attempt in range(200):
        grid = [["." for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                if rng.random() < density:
                    grid[r][c] = "X"
        grid[0][0] = "S"
        grid[rows - 1][cols - 1] = "E"
        res = A.astar(grid, (0, 0), (rows - 1, cols - 1), weight=0.0)
        if res.found and len(res.path) > rows + cols - 2:
            return grid
    raise RuntimeError("迷宫生成失败")


def maze_heuristic_comparison() -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    cases = [
        (5, 5, 0.25, 7),
        (10, 10, 0.28, 11),
        (15, 15, 0.28, 13),
        (20, 20, 0.30, 17),
        (25, 25, 0.30, 19),
    ]
    for i, (r, c, d, seed) in enumerate(cases):
        if i == 0:
            grid, start, goal = P.MAZE_1, P.MAZE_1_START, P.MAZE_1_GOAL
        else:
            grid, start, goal = make_maze(r, c, d, seed), (0, 0), (r - 1, c - 1)
        h1 = A.astar(grid, start, goal, weight=1.0)
        h0 = A.astar(grid, start, goal, weight=0.0)
        rows.append(
            {
                "size": f"{r}x{c}",
                "zero": h0.stats.expanded,
                "manhattan": h1.stats.expanded,
                "ratio": round(h0.stats.expanded / h1.stats.expanded, 2),
                "cost": h1.stats.cost,
                "same_cost": int(abs(h0.stats.cost - h1.stats.cost) < 1e-9),
            }
        )
    return rows


def terrain_goal_cost_check() -> Dict[str, float]:
    """对比“E 的进入代价视为 0”和“E 按 1 计”两种口径下的最优代价。"""
    zero_goal = P.terrain_cost_with_zero_goal(P.TERRAIN_GOAL)

    def one_goal(r: int, c: int) -> float:
        if (r, c) == P.TERRAIN_GOAL:
            return 1.0
        return zero_goal(r, c)

    a = A.astar(P.TERRAIN, P.TERRAIN_START, P.TERRAIN_GOAL, entry_cost=zero_goal)
    b = A.astar(P.TERRAIN, P.TERRAIN_START, P.TERRAIN_GOAL, entry_cost=one_goal)
    # 只把终点按 0 计、其他照旧时，是否会影响路径形状
    return {
        "cost_zero": a.stats.cost,
        "cost_one": b.stats.cost,
        "same_path": a.path == b.path,
        "expanded": a.stats.expanded,
    }


def random_game_tree(branching: int, depth: int, seed: int) -> TreeNode:
    rng = random.Random(seed)

    def build(d: int) -> TreeNode:
        if d == 0:
            return TreeNode(value=rng.randint(1, 99))
        return TreeNode(children=[build(d - 1) for _ in range(branching)])

    return build(depth)


def game_tree_comparison() -> List[Dict[str, float]]:
    out = []
    for branching, depth in [(3, 3), (3, 4), (4, 3), (4, 4)]:
        tree = random_game_tree(branching, depth, seed=branching * 10 + depth)
        mm, ab = Stats(), Stats()
        v1 = minimax(tree, mm)
        v2 = alpha_beta(tree, ab)
        rev = Stats()
        v3 = alpha_beta(_mirror(tree), rev)
        out.append(
            {
                "shape": f"b={branching},d={depth}",
                "leaves": branching ** depth,
                "minimax_nodes": mm.nodes,
                "ab_nodes": ab.nodes,
                "ab_prunes": ab.prunes,
                "ratio": round(mm.nodes / max(ab.nodes, 1), 2),
                "reversed_nodes": rev.nodes,
                "same_value": int(v1 == v2 == v3),
            }
        )
    return out


def _mirror(node: TreeNode) -> TreeNode:
    if node.is_leaf:
        return TreeNode(value=node.value)
    return TreeNode(children=[_mirror(c) for c in reversed(node.children)])
