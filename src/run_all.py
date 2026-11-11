"""运行全部测试用例、输出结果并保存实验数据。

用法（在项目根目录）：
    python -m src.run_all
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from . import astar as A
from . import experiments as E
from . import problems as P
from .minimax import build_demo_tree, alpha_beta, minimax, Stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"

_lines: List[str] = []


def log(text: str = "") -> None:
    print(text)
    _lines.append(text)


def fmt_path(path) -> str:
    return " -> ".join(f"({r},{c})" for r, c in path)


def main() -> Dict[str, Any]:
    OUT.mkdir(exist_ok=True)
    data: Dict[str, Any] = {}

    log("=== 实验二 搜索算法 · 测试用例运行结果 ===")
    log("")

    # ---------------- 题目一
    r1 = P.solve_problem1()
    log("[题目一] 迷宫寻路（A*, 曼哈顿距离）")
    log(f"  路径: {fmt_path(r1['path'])}")
    log(f"  路径步数: {r1['cost']}    扩展节点: {r1['expanded']}    (h=0 时: {r1['expanded_zero_h']})")
    assert r1["path"][0] == (0, 0) and r1["path"][-1] == (3, 4) and r1["cost"] == 7
    assert r1["cost"] == len(r1["path"]) - 1
    # 用独立函数复算路径代价，与搜索中累计的 g 值对照
    assert abs(A.path_cost(r1["path"], lambda r, c: 1.0, P.MAZE_1_START) - r1["cost"]) < 1e-9
    log("  √ 与预期输出一致")
    log("")

    # ---------------- 题目二
    r2 = P.solve_problem2()
    log("[题目二] 加权地形（A*, 地形代价）")
    log(f"  路径: {fmt_path(r2['path'])}")
    log(f"  最小总代价: {int(r2['cost'])}    扩展节点: {r2['expanded']}    (h=0 时: {r2['expanded_zero_h']})")
    log("  逐步累计: " + "  ".join(f"({r},{c}):+{int(s)}={int(t)}" for (r, c), s, t in r2["steps"][1:]))
    assert int(r2["cost"]) == 7
    _tc = P.terrain_cost_with_zero_goal(P.TERRAIN_GOAL)
    assert abs(A.path_cost(r2["path"], _tc, P.TERRAIN_START) - r2["cost"]) < 1e-9
    log("  √ 与预期输出一致（代价 7）")
    log("")

    # ---------------- 题目三
    r3 = P.solve_problem3()
    log("[题目三] 极大极小博弈树（Alpha-Beta 剪枝）")
    log(f"  MAX 最优得分: {int(r3['minimax'])}")
    log(f"  Minimax  : 结果 {int(r3['minimax'])}，访问 {r3['minimax_stats']['nodes']} 个节点")
    log(f"  Alpha-Beta: 结果 {int(r3['alpha_beta'])}，访问 {r3['alpha_beta_stats']['nodes']} 个节点，"
        f"剪枝 {r3['alpha_beta_stats']['prunes']} 次")
    log(f"  子节点反向访问: 结果 {int(r3['reversed_value'])}，访问 {r3['reversed_stats']['nodes']} 个节点")
    assert int(r3["minimax"]) == 5 == int(r3["alpha_beta"])
    log("  √ 与预期输出一致（5）")
    log("")

    # ---------------- 题目四
    matrix, paths = P.distance_matrix()
    log("[题目四] 竞争环境下的宝藏分配（综合题）")
    log("  6x6 最小移动代价矩阵（行/列顺序: A, B, T1, T2, T3, T4）:")
    log("        " + "".join(f"{n:>6}" for n in P.NODES))
    for name, row in zip(P.NODES, matrix):
        log(f"    {name:<4}" + "".join(f"{int(v):>6}" for v in row))
    r4 = P.solve_problem4(matrix)
    for depth in (2, 4):
        mm = r4[f"h{depth}_minimax"]
        ab = r4[f"h{depth}_alpha-beta"]
        log(f"  H={depth}: Minimax -> {mm['best_target']}, {int(mm['best_value'])} "
            f"(节点 {mm['nodes']})")
        log(f"  H={depth}: Alpha-Beta -> {ab['best_target']}, {int(ab['best_value'])} "
            f"(节点 {ab['nodes']}, 剪枝 {ab['prunes']})")
        assert ab["best_target"] == mm["best_target"] == ("T2" if depth == 2 else "T3")
        assert int(ab["best_value"]) == (-1 if depth == 2 else 3)
    log("  √ 与预期输出一致（H=2: T2/-1, H=4: T3/3）")
    log("")

    # ---------------- 对照实验
    log("[对照实验]")
    maze_rows = E.maze_heuristic_comparison()
    for row in maze_rows:
        log(f"  迷宫 {row['size']:>5}: h=0 扩展 {int(row['zero']):>5}，曼哈顿扩展 {int(row['manhattan']):>5}，"
            f"约 {row['ratio']:.2f} 倍")
    terrain_check = E.terrain_goal_cost_check()
    log(f"  题目二：E 按 0 计代价 {int(terrain_check['cost_zero'])}，按 1 计代价 {int(terrain_check['cost_one'])}，"
        f"路径相同: {terrain_check['same_path']}")
    tree_rows = E.game_tree_comparison()
    for row in tree_rows:
        log(f"  博弈树 {row['shape']}: 叶子 {int(row['leaves'])}，Minimax {int(row['minimax_nodes'])} 节点，"
            f"Alpha-Beta {int(row['ab_nodes'])} 节点")
    log("")
    log("全部用例通过：题目一 7 步、题目二 代价 7、题目三 5、题目四 H=2 → T2/-1，H=4 → T3/3")

    data = {
        "problem1": {k: v for k, v in r1.items() if k not in ("order", "order_zero_h")},
        "problem1_order": [list(x) for x in r1["order"]],
        "problem1_order_zero": [list(x) for x in r1["order_zero_h"]],
        "problem2": {k: v for k, v in r2.items() if k != "order"},
        "problem2_order": [list(x) for x in r2["order"]],
        "problem2_steps": [[list(c), s, t] for c, s, t in r2["steps"]],
        "problem3": r3,
        "problem4": r4,
        "matrix": matrix,
        "matrix_paths": {f"{k[0]}->{k[1]}": [list(x) for x in v] for k, v in paths.items()},
        "maze_rows": maze_rows,
        "terrain_check": terrain_check,
        "tree_rows": tree_rows,
    }
    (OUT / "results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "run_log.txt").write_text("\n".join(_lines) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    main()
