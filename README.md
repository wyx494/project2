# 实验二　搜索算法（A\* / Minimax / Alpha-Beta）

当代人工智能实验课 · 实验二。四道题共用一套 A\* 与博弈搜索实现，所有输出按实验指导给出的用例格式。

## 运行

```bash
python -m src.run_all
```

Python 3.9+，只用标准库（heapq、dataclasses），不需要安装任何第三方包。
运行后会打印四道题的结果并与预期输出逐条比对，同时把数据写入 `results/results.json` 和 `results/run_log.txt`。

## 目录结构

```
search-lab/
├─ src/
│  ├─ astar.py        通用 A*（可替换启发函数与“进入某格的代价”）
│  ├─ minimax.py      Minimax 与 Alpha-Beta 剪枝、示例博弈树
│  ├─ problems.py     四道题的数据与求解器（含宝藏博弈的 Minimax 搜索）
│  ├─ experiments.py  报告里的对照实验（迷宫规模、终点代价、随机博弈树）
│  └─ run_all.py      一次跑完四题 + 对照实验，输出并校验
├─ tools/
│  ├─ make_figures.py 用 PIL 生成报告插图
│  └─ build_report.py 生成报告 docx（再由 LibreOffice 转 PDF）
├─ results/           运行结果（results.json、run_log.txt）
└─ report/            报告 docx / pdf 与插图
```

## 四道题

| 题目 | 内容 | 用例结果 |
| --- | --- | --- |
| 一 | 5×5 迷宫，A\* + 曼哈顿距离求最短路 | 7 步 |
| 二 | 加权地形，进入格子的代价为地形值，终点代价按 0 计 | 总代价 7 |
| 三 | 极大极小博弈树，Alpha-Beta 剪枝求 MAX 最优得分 | 5 |
| 四 | A\* 求 6×6 距离矩阵 + Minimax/Alpha-Beta 求宝藏分配最优首步 | H=2 → T2 / −1；H=4 → T3 / 3 |

## 实现要点

- **A\***：状态为 `(row, col)`，`f = g + h`，`h` 为曼哈顿距离；开放表用二叉堆并带自增序号保证同分时的先进先出，闭表防止重复扩展。代价统一在“进入某格”时结算，因此题目一、题目二、题目四的距离计算共用同一个函数。
- **Minimax / Alpha-Beta**：根节点为 MAX，逐层交替；`alpha_beta()` 在更新 α/β 之后判剪枝，并统计访问节点数与剪枝次数。
- **题目四**：状态为 `(A 位置, B 位置, 剩余宝藏, A 收益, B 收益, 当前玩家)`，每步按 `Gain = V − d` 结算，终局返回 `Score_A − Score_B`；搜索前先用 A\* 求出 6×6 距离矩阵。

## 复现说明

随机迷宫、随机博弈树都使用固定随机种子（见 `src/experiments.py`），重复运行结果不变。
