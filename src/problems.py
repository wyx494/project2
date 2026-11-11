"""实验二四个题目的数据与求解入口。

题目一：迷宫寻路（A*，单位代价）
题目二：加权地形（A*，地形代价）
题目三：极大极小博弈树（Minimax / Alpha-Beta）
题目四：竞争环境下的宝藏分配（综合题）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import astar as A
from .minimax import Stats, TreeNode, alpha_beta, build_demo_tree, minimax

Coord = Tuple[int, int]

# ---------------------------------------------------------------- 题目一
MAZE_1: List[List[str]] = [
    ["S", ".", ".", "X", "."],
    [".", "X", ".", ".", "."],
    [".", "X", ".", "X", "."],
    [".", ".", ".", "X", "E"],
    ["X", "X", ".", ".", "."],
]
MAZE_1_START: Coord = (0, 0)
MAZE_1_GOAL: Coord = (3, 4)

# ---------------------------------------------------------------- 题目二
TERRAIN: List[List[str]] = [
    ["S", "1", "1", "8", "1"],
    ["1", "8", "3", "1", "1"],
    ["1", "8", "1", "8", "1"],
    ["1", "1", "1", "8", "1"],
    ["8", "8", "1", "1", "E"],
]
TERRAIN_START: Coord = (0, 0)
TERRAIN_GOAL: Coord = (4, 4)

# ---------------------------------------------------------------- 题目四
TREASURE_MAP: List[List[str]] = [
    ["A", "1", "1", "X", "2", "1", "T1"],
    ["1", "X", "6", "X", "1", "X", "1"],
    ["1", "1", "T2", "1", "1", "1", "1"],
    ["X", "1", "X", "8", "X", "1", "X"],
    ["1", "1", "1", "1", "T3", "1", "1"],
    ["1", "X", "9", "X", "1", "X", "1"],
    ["T4", "1", "1", "X", "1", "1", "B"],
]
START_A: Coord = (0, 0)
START_B: Coord = (6, 6)
TREASURES: Dict[str, Tuple[Coord, int]] = {
    "T1": ((0, 6), 9),
    "T2": ((2, 2), 6),
    "T3": ((4, 4), 7),
    "T4": ((6, 0), 7),
}
NODES: List[str] = ["A", "B", "T1", "T2", "T3", "T4"]
NODE_POS: Dict[str, Coord] = {"A": START_A, "B": START_B, **{k: v[0] for k, v in TREASURES.items()}}


def treasure_cost(grid):
    """题目四的进入代价：数字格按数字，A/B/T 格按 1，X 不可通行。"""

    def cost(r: int, c: int) -> float:
        v = str(grid[r][c])
        if v.isdigit():
            return float(int(v))
        return 1.0

    return cost


def terrain_cost_with_zero_goal(goal: Coord):
    """题目二的进入代价：地形数字；终点 E 的进入代价按题意视为 0。"""

    def cost(r: int, c: int) -> float:
        if (r, c) == goal:
            return 0.0
        v = str(TERRAIN[r][c])
        return float(int(v)) if v.isdigit() else 1.0

    return cost


# ---------------------------------------------------------------- 求解器
def solve_problem1(check_h_zero: bool = True) -> Dict[str, object]:
    res = A.astar(MAZE_1, MAZE_1_START, MAZE_1_GOAL, weight=1.0, keep_order=True)
    out: Dict[str, object] = {
        "path": res.path,
        "cost": len(res.path) - 1,
        "expanded": res.stats.expanded,
        "generated": res.stats.generated,
    }
    if check_h_zero:
        zero = A.astar(MAZE_1, MAZE_1_START, MAZE_1_GOAL, weight=0.0, keep_order=True)
        out["expanded_zero_h"] = zero.stats.expanded
        out["generated_zero_h"] = zero.stats.generated
        out["order_zero_h"] = zero.order
    out["order"] = res.order
    return out


def solve_problem2() -> Dict[str, object]:
    cost = terrain_cost_with_zero_goal(TERRAIN_GOAL)
    res = A.astar(TERRAIN, TERRAIN_START, TERRAIN_GOAL, entry_cost=cost, keep_order=True)
    # 逐步累计代价，用于报告里的过程展示
    steps = []
    total = 0.0
    for i, cell in enumerate(res.path):
        step_cost = 0.0 if i == 0 else cost(*cell)
        total += step_cost
        steps.append((cell, step_cost, total))
    naive = A.astar(TERRAIN, TERRAIN_START, TERRAIN_GOAL, entry_cost=cost, weight=0.0, keep_order=True)
    return {
        "path": res.path,
        "cost": total,
        "expanded": res.stats.expanded,
        "generated": res.stats.generated,
        "steps": steps,
        "expanded_zero_h": naive.stats.expanded,
        "order": res.order,
    }


def solve_problem3() -> Dict[str, object]:
    root = build_demo_tree()
    mm_stats, ab_stats = Stats(), Stats()
    mm_value = minimax(root, mm_stats)
    ab_value = alpha_beta(root, ab_stats)
    rev_stats = Stats()
    ab_rev = alpha_beta(_reverse(root), rev_stats)
    return {
        "minimax": mm_value,
        "alpha_beta": ab_value,
        "minimax_stats": mm_stats.as_dict(),
        "alpha_beta_stats": ab_stats.as_dict(),
        "reversed_value": ab_rev,
        "reversed_stats": rev_stats.as_dict(),
    }


def _reverse(node: TreeNode) -> TreeNode:
    if node.is_leaf:
        return TreeNode(value=node.value)
    return TreeNode(children=[_reverse(c) for c in reversed(node.children)])


def distance_matrix() -> Tuple[List[List[float]], Dict[Tuple[str, str], List[Coord]]]:
    """A* 求 A、B、T1..T4 两两之间的最小移动代价，返回 6x6 矩阵与路径。"""
    grid = TREASURE_MAP
    cost = treasure_cost(grid)
    n = len(NODES)
    matrix = [[0.0] * n for _ in range(n)]
    paths: Dict[Tuple[str, str], List[Coord]] = {}
    for i, src in enumerate(NODES):
        for j, dst in enumerate(NODES):
            if i == j:
                continue
            res = A.astar(grid, NODE_POS[src], NODE_POS[dst], entry_cost=cost)
            matrix[i][j] = res.stats.cost if res.found else float("inf")
            paths[(src, dst)] = res.path
    return matrix, paths


@dataclass
class GameState:
    pos_a: Coord
    pos_b: Coord
    remaining: Tuple[str, ...]
    score_a: float
    score_b: float
    player: str  # "A" 或 "B"


class TreasureGame:
    """题目四的博弈：A(MAX) 与 B(MIN) 轮流选宝藏，移动到宝藏处并把收益记入总分。"""

    def __init__(self, matrix: List[List[float]], values: Dict[str, int], order: str = "natural"):
        self.index = {name: i for i, name in enumerate(NODES)}
        self.matrix = matrix
        self.values = values
        self.order = order

    def dist(self, src: str, dst: str) -> float:
        return self.matrix[self.index[src]][self.index[dst]]

    def gains(self, pos_key: str, remaining: Tuple[str, ...]) -> List[Tuple[str, float]]:
        return [(t, self.values[t] - self.dist(pos_key, t)) for t in remaining]

    def solve(self, depth: int, algorithm: str = "alpha-beta", order: str = "natural") -> Dict[str, object]:
        """返回 A 的最优首步、该步对应的收益差，以及搜索开销。"""
        self.order = order
        start = GameState(START_A, START_B, tuple(TREASURES), 0.0, 0.0, "A")
        nodes = {"n": 0}
        prunes = {"n": 0}
        best_value = -float("inf")
        best_target = None
        detail = {}

        for target, gain in self._ordered(self.gains("A", start.remaining), order):
            remaining = tuple(t for t in start.remaining if t != target)
            child = GameState(TREASURES[target][0], start.pos_b, remaining, start.score_a + gain, 0.0, "B")
            if algorithm == "minimax":
                value = self._minimax(child, depth - 1, nodes)
            else:
                value = self._alpha_beta(child, -float("inf"), float("inf"), depth - 1, nodes, prunes)
            detail[target] = round(value, 3)
            if value > best_value:
                best_value, best_target = value, target

        return {
            "depth": depth,
            "algorithm": algorithm,
            "order": order,
            "best_target": best_target,
            "best_value": round(best_value, 3),
            "values": detail,
            "nodes": nodes["n"],
            "prunes": prunes["n"],
        }

    def _ordered(self, moves: List[Tuple[str, float]], order: str):
        if order == "natural":
            return moves
        if order == "gain_desc":
            return sorted(moves, key=lambda x: -x[1])
        if order == "gain_asc":
            return sorted(moves, key=lambda x: x[1])
        raise ValueError(order)

    def _minimax(self, state: GameState, depth: int, nodes: Dict[str, int]) -> float:
        nodes["n"] += 1
        if depth <= 0 or not state.remaining:
            return state.score_a - state.score_b
        moves = self._ordered(self.gains(state.player, state.remaining), self.order)
        if state.player == "A":
            return max(self._child(state, t, g, depth, nodes) for t, g in moves)
        return min(self._child(state, t, g, depth, nodes) for t, g in moves)

    def _child(self, state: GameState, target: str, gain: float, depth: int, nodes: Dict[str, int]) -> float:
        remaining = tuple(t for t in state.remaining if t != target)
        if state.player == "A":
            nxt = GameState(TREASURES[target][0], state.pos_b, remaining, state.score_a + gain, state.score_b, "B")
        else:
            nxt = GameState(state.pos_a, TREASURES[target][0], remaining, state.score_a, state.score_b + gain, "A")
        return self._minimax(nxt, depth - 1, nodes)

    def _alpha_beta(self, state: GameState, alpha: float, beta: float, depth: int, nodes, prunes) -> float:
        nodes["n"] += 1
        if depth <= 0 or not state.remaining:
            return state.score_a - state.score_b
        moves = self._ordered(self.gains(state.player, state.remaining), self.order)
        if state.player == "A":
            value = -float("inf")
            for t, g in moves:
                value = max(value, self._child_ab(state, t, g, alpha, beta, depth, nodes, prunes))
                alpha = max(alpha, value)
                if alpha >= beta:
                    prunes["n"] += 1
                    break
            return value
        value = float("inf")
        for t, g in moves:
            value = min(value, self._child_ab(state, t, g, alpha, beta, depth, nodes, prunes))
            beta = min(beta, value)
            if alpha >= beta:
                prunes["n"] += 1
                break
        return value

    def _child_ab(self, state, target, gain, alpha, beta, depth, nodes, prunes) -> float:
        remaining = tuple(t for t in state.remaining if t != target)
        if state.player == "A":
            nxt = GameState(TREASURES[target][0], state.pos_b, remaining, state.score_a + gain, state.score_b, "B")
        else:
            nxt = GameState(state.pos_a, TREASURES[target][0], remaining, state.score_a, state.score_b + gain, "A")
        return self._alpha_beta(nxt, alpha, beta, depth - 1, nodes, prunes)


def solve_problem4(matrix: Optional[List[List[float]]] = None) -> Dict[str, object]:
    matrix = matrix or distance_matrix()[0]
    game = TreasureGame(matrix, {k: v[1] for k, v in TREASURES.items()})
    out: Dict[str, object] = {}
    for depth in (2, 4):
        for algo in ("minimax", "alpha-beta"):
            out[f"h{depth}_{algo}"] = game.solve(depth, algo)
    out["h2_order_desc"] = game.solve(2, "alpha-beta", order="gain_desc")
    out["h4_order_desc"] = game.solve(4, "alpha-beta", order="gain_desc")
    return out
