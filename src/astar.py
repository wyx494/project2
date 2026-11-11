"""A* 搜索的通用实现。

支持：
- 任意二维网格（字符 / 整数）；
- 自定义“进入某格的代价”函数（用于题目二的地形代价、题目四的宝藏格代价）；
- 曼哈顿启发（可带权重），也可以换成其他启发函数；
- 统计扩展节点数、生成节点数，便于做对照实验。
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

Coord = Tuple[int, int]
Grid = Sequence[Sequence[object]]

FOUR_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
EIGHT_DIRS = FOUR_DIRS + [(-1, -1), (-1, 1), (1, -1), (1, 1)]

BLOCKED = {"X", "X".lower(), "#"}


@dataclass
class SearchStats:
    """一次搜索的统计量。"""

    expanded: int = 0          # 从优先队列中弹出并处理的节点数
    generated: int = 0         # 入过队的节点数
    max_frontier: int = 0      # 优先队列的历史最大长度
    cost: float = 0.0          # 路径总代价


@dataclass
class SearchResult:
    path: List[Coord] = field(default_factory=list)
    stats: SearchStats = field(default_factory=SearchStats)
    order: List[Coord] = field(default_factory=list)  # 扩展顺序，用于画图

    @property
    def found(self) -> bool:
        return bool(self.path)


def default_entry_cost(grid: Grid) -> Callable[[int, int], float]:
    """默认代价：数字格按数字算，其它可通行格算 1。"""

    def cost(r: int, c: int) -> float:
        v = grid[r][c]
        if isinstance(v, str) and v.isdigit():
            return float(int(v))
        return 1.0

    return cost


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(
    grid: Grid,
    start: Coord,
    goal: Coord,
    entry_cost: Optional[Callable[[int, int], float]] = None,
    weight: float = 1.0,
    diagonal: bool = False,
    keep_order: bool = False,
) -> SearchResult:
    """在 grid 上求 start -> goal 的最小代价路径。

    entry_cost(r, c) 表示“走进 (r, c) 这一格”要付的代价；起点格不计代价。
    weight 为启发函数权重：1.0 表示标准（可采纳的）曼哈顿距离。
    """
    rows, cols = len(grid), len(grid[0])
    cost_of = entry_cost or default_entry_cost(grid)
    dirs = EIGHT_DIRS if diagonal else FOUR_DIRS

    def passable(r: int, c: int) -> bool:
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        return str(grid[r][c]) not in BLOCKED

    if not passable(*start) or not passable(*goal):
        return SearchResult()

    def h(r: int, c: int) -> float:
        return weight * manhattan((r, c), goal)

    stats = SearchStats()
    order: List[Coord] = []

    counter = 0
    open_heap: List[Tuple[float, int, Coord]] = []
    start_h = h(*start)
    heapq.heappush(open_heap, (start_h, counter, start))
    counter += 1
    stats.generated += 1

    g_score: Dict[Coord, float] = {start: 0.0}
    came: Dict[Coord, Coord] = {}
    closed: set[Coord] = set()

    while open_heap:
        stats.max_frontier = max(stats.max_frontier, len(open_heap))
        _, _, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        stats.expanded += 1
        if keep_order:
            order.append(cur)

        if cur == goal:
            path = _reconstruct(came, start, goal)
            stats.cost = g_score[goal]
            return SearchResult(path=path, stats=stats, order=order)

        cr, cc = cur
        for dr, dc in dirs:
            nr, nc = cr + dr, cc + dc
            if not passable(nr, nc):
                continue
            nxt = (nr, nc)
            if nxt in closed:
                continue
            step = cost_of(nr, nc)
            if diagonal and dr != 0 and dc != 0:
                step *= 1.0  # 本实验不使用对角线移动
            tentative = g_score[cur] + step
            if tentative < g_score.get(nxt, float("inf")) - 1e-12:
                g_score[nxt] = tentative
                came[nxt] = cur
                counter += 1
                heapq.heappush(open_heap, (tentative + h(nr, nc), counter, nxt))
                stats.generated += 1

    return SearchResult(path=[], stats=stats, order=order)


def _reconstruct(came: Dict[Coord, Coord], start: Coord, goal: Coord) -> List[Coord]:
    path = [goal]
    node = goal
    while node != start:
        node = came[node]
        path.append(node)
    path.reverse()
    return path


def path_cost(path: Sequence[Coord], entry_cost: Callable[[int, int], float], start: Coord) -> float:
    """按“进入目标格的代价”独立复算一条路径的代价，用于交叉验证。"""
    total = 0.0
    for i in range(1, len(path)):
        total += entry_cost(*path[i])
    return total
