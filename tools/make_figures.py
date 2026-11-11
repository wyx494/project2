"""用 PIL 生成报告里的插图（不依赖 matplotlib）。

输出到 report/figures/*.png。所有图都基于 results/results.json 与 results/run_log.txt
的真实运行结果绘制。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
FIG = ROOT / "report" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

CN = r"C:\Windows\Fonts\msyh.ttc"
CN_B = r"C:\Windows\Fonts\msyhbd.ttc"
MONO = r"C:\Windows\Fonts\consola.ttf"

DPI = 300
WHITE = (255, 255, 255)
INK = (33, 37, 41)
MUTED = (110, 116, 122)
BLUE = (32, 96, 200)


def px(cm: float) -> int:
    return int(round(cm / 2.54 * DPI))


def F(path: str, size_px: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size_px)


def arrow(draw: ImageDraw.ImageDraw, p1, p2, color=INK, w=4, head=13):
    draw.line([p1, p2], fill=color, width=w)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for delta in (math.radians(150), math.radians(-150)):
        x = p2[0] + head * math.cos(ang + delta)
        y = p2[1] + head * math.sin(ang + delta)
        draw.line([p2, (x, y)], fill=color, width=w)


# ------------------------------------------------------------------ 图 1：迷宫
def fig_maze(data: Dict) -> Path:
    maze = [
        ["S", ".", ".", "X", "."],
        [".", "X", ".", ".", "."],
        [".", "X", ".", "X", "."],
        [".", ".", ".", "X", "E"],
        ["X", "X", ".", ".", "."],
    ]
    path = [tuple(p) for p in data["problem1"]["path"]]
    order_zero = {tuple(p) for p in data["problem1_order_zero"]}
    order_h = {tuple(p) for p in data["problem1_order"]}
    n_zero = int(data["problem1"]["expanded_zero_h"])
    n_h = int(data["problem1"]["expanded"])

    cell = px(1.15)
    gap = px(1.15)
    pad = px(0.5)
    w = 3 * (5 * cell + 2 * pad) + 2 * gap + 2 * pad
    title_h = px(0.75)
    cap_h = px(0.85)
    h = title_h + 5 * cell + 2 * pad + cap_h

    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    f_cell = F(CN_B, int(cell * 0.5))
    f_cap = F(CN, int(cell * 0.30))

    titles = ["最短路径（7 步）", f"h = 0：扩展 {n_zero} 个节点", f"曼哈顿距离：扩展 {n_h} 个节点"]
    fills = [None, order_zero, order_h]

    for k in range(3):
        x0 = pad + k * (5 * cell + 2 * pad + gap)
        y0 = title_h
        d.text((x0 + 2.5 * cell, title_h * 0.45), titles[k], font=f_cell, fill=INK, anchor="mm")

        for r in range(5):
            for c in range(5):
                v = maze[r][c]
                x1 = x0 + pad + c * cell
                y1 = y0 + pad + r * cell
                x2, y2 = x1 + cell, y1 + cell
                if v == "X":
                    fill, txt, tcol = (74, 79, 88), "X", WHITE
                elif v == "S":
                    fill, txt, tcol = (146, 208, 150), "S", INK
                elif v == "E":
                    fill, txt, tcol = (238, 153, 146), "E", INK
                else:
                    fill, txt, tcol = (247, 249, 252), "", INK
                    if fills[k] and (r, c) in fills[k]:
                        fill = (255, 226, 176) if k == 1 else (196, 233, 200)
                d.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill=fill, outline=(210, 214, 220), width=2)
                if txt:
                    d.text(((x1 + x2) / 2, (y1 + y2) / 2), txt, font=f_cell, fill=tcol, anchor="mm")

        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            p1 = (x0 + pad + a[1] * cell + cell / 2, y0 + pad + a[0] * cell + cell / 2)
            p2 = (x0 + pad + b[1] * cell + cell / 2, y0 + pad + b[0] * cell + cell / 2)
            arrow(d, p1, p2, color=BLUE, w=max(4, cell // 22), head=cell // 6)

        cap = ["", "橙色：搜索过程中被展开的格子", "绿色：搜索过程中被展开的格子"][k]
        d.text((x0 + 2.5 * cell, y0 + 5 * cell + pad + cap_h * 0.45), cap, font=f_cap, fill=MUTED, anchor="mm")

    out = FIG / "fig1_maze.png"
    img.save(out, dpi=(DPI, DPI))
    return out


# ------------------------------------------------------------------ 图 2：加权地形
def fig_terrain(data: Dict) -> Path:
    grid = [
        ["S", "1", "1", "8", "1"],
        ["1", "8", "3", "1", "1"],
        ["1", "8", "1", "8", "1"],
        ["1", "1", "1", "8", "1"],
        ["8", "8", "1", "1", "E"],
    ]
    steps = [(tuple(c), int(s), int(t)) for c, s, t in data["problem2_steps"]]
    path = [c for c, _, _ in steps]
    cumulative = {c: t for c, _, t in steps}
    seq = {c: i for i, (c, _, _) in enumerate(steps)}

    cell = px(1.62)
    pad = px(0.42)
    label_w = px(0.75)
    w = label_w + 5 * cell + 2 * pad
    h = 5 * cell + 2 * pad + px(0.10)
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    f_cell = F(CN_B, int(cell * 0.40))
    f_badge = F(CN_B, int(cell * 0.17))
    f_row = F(CN, int(cell * 0.20))

    def color(v: int):
        t = min(1.0, max(0.0, (v - 1) / 7))
        return (int(250 - 62 * t), int(246 - 118 * t), int(236 - 150 * t))

    for r in range(5):
        d.text((label_w * 0.45, pad + r * cell + cell / 2), str(r), font=f_row, fill=MUTED, anchor="mm")
        for c in range(5):
            x1 = label_w + pad + c * cell
            y1 = pad + r * cell
            x2, y2 = x1 + cell, y1 + cell
            v = grid[r][c]
            in_path = (r, c) in seq
            if v == "X":
                fill, txt, tcol = (74, 79, 88), "X", WHITE
            elif v == "S":
                fill, txt, tcol = (146, 208, 150), "S", INK
            elif v == "E":
                fill, txt, tcol = (238, 153, 146), "E", INK
            else:
                fill, txt, tcol = color(int(v)), v, INK
            d.rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], fill=fill,
                        outline=BLUE if in_path else (205, 209, 216), width=5 if in_path else 2)
            d.text(((x1 + x2) / 2, (y1 + y2) / 2 + cell * 0.06), txt, font=f_cell, fill=tcol, anchor="mm")
            if in_path:
                d.text((x1 + cell * 0.12, y1 + cell * 0.14), str(seq[(r, c)]), font=f_badge,
                       fill=(20, 70, 170), anchor="lt")
                d.text((x2 - cell * 0.10, y1 + cell * 0.14), str(cumulative[(r, c)]), font=f_badge,
                       fill=(20, 70, 170), anchor="rt")

    d.text((w / 2, px(0.10)), "", font=F(CN, 10), fill=MUTED, anchor="mm")

    out = FIG / "fig3_terrain.png"
    img.save(out, dpi=(DPI, DPI))
    return out


# ------------------------------------------------------------------ 图 3：节点数对比
def fig_nodes(data: Dict) -> Path:
    rows = data["maze_rows"]
    w, h = px(14.5), px(5.2)
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)

    left, right = px(1.6), px(0.4)
    top, bottom = px(0.75), px(1.15)
    plot_w, plot_h = w - left - right, h - top - bottom
    maxv = max(r["zero"] for r in rows) * 1.18

    f_lab = F(CN, int(px(0.30)))
    f_val = F(CN_B, int(px(0.27)))
    f_leg = F(CN, int(px(0.30)))

    for i in range(5):
        y = top + plot_h - plot_h * i / 4
        d.line([(left, y), (left + plot_w, y)], fill=(232, 235, 240), width=2)
        d.text((left - px(0.15), y), str(int(maxv * i / 4)), font=f_lab, fill=MUTED, anchor="rm")

    n = len(rows)
    group_w = plot_w / n
    bw = group_w * 0.24

    for i, row in enumerate(rows):
        cx = left + group_w * (i + 0.5)
        for j, (key, col) in enumerate([("zero", (188, 196, 206)), ("manhattan", (58, 118, 214))]):
            v = row[key]
            bh = plot_h * v / maxv
            x1 = cx - bw - px(0.05) + j * (bw + px(0.10))
            d.rectangle([x1, top + plot_h - bh, x1 + bw, top + plot_h], fill=col)
            d.text((x1 + bw / 2, top + plot_h - bh - px(0.12)), f"{int(v)}", font=f_val, fill=INK, anchor="mb")
        d.text((cx, top + plot_h + px(0.18)), row["size"], font=f_lab, fill=INK, anchor="mt")

    d.text((left + plot_w / 2, h - px(0.25)), "迷宫规模", font=f_lab, fill=MUTED, anchor="mm")
    lx = left + plot_w - px(4.0)
    d.rectangle([lx, px(0.18), lx + px(0.28), px(0.45)], fill=(188, 196, 206))
    d.text((lx + px(0.38), px(0.32)), "h = 0", font=f_leg, fill=INK, anchor="lm")
    d.rectangle([lx + px(1.35), px(0.18), lx + px(1.63), px(0.45)], fill=(58, 118, 214))
    d.text((lx + px(1.73), px(0.32)), "曼哈顿距离", font=f_leg, fill=INK, anchor="lm")

    out = FIG / "fig2_nodes.png"
    img.save(out, dpi=(DPI, DPI))
    return out


# ------------------------------------------------------------------ 图 4：距离矩阵
def fig_matrix(data: Dict) -> Path:
    names = ["A", "B", "T1", "T2", "T3", "T4"]
    matrix = data["matrix"]
    cell = px(1.05)
    left = px(1.35)
    top = px(1.15)
    w = left + 6 * cell + px(0.35)
    h = top + 6 * cell + px(0.35)
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    f = F(CN_B, int(cell * 0.34))
    fh = F(CN_B, int(cell * 0.32))
    f_lab = F(CN, int(cell * 0.26))

    d.text((left + 3 * cell, top * 0.32), "目标", font=f_lab, fill=MUTED, anchor="mm")
    d.text((px(0.45), top + 3 * cell), "起点", font=f_lab, fill=MUTED, anchor="mm")

    for i, name in enumerate(names):
        d.text((left * 0.55, top + i * cell + cell / 2), name, font=fh, fill=INK, anchor="mm")
        d.text((left + i * cell + cell / 2, top * 0.72), name, font=fh, fill=INK, anchor="mm")

    for i in range(6):
        for j in range(6):
            v = matrix[i][j]
            x1, y1 = left + j * cell, top + i * cell
            if i == j:
                fill = (232, 235, 240)
            else:
                t = v / 12.0
                fill = (int(252 - 92 * t), int(250 - 118 * t), int(240 - 78 * t))
            d.rectangle([x1 + 2, y1 + 2, x1 + cell - 2, y1 + cell - 2], fill=fill,
                        outline=(205, 209, 216), width=2)
            d.text((x1 + cell / 2, y1 + cell / 2), str(int(v)), font=f, fill=INK, anchor="mm")

    out = FIG / "fig4_matrix.png"
    img.save(out, dpi=(DPI, DPI))
    return out


# ------------------------------------------------------------------ 图 5：运行截图
def _advance(text: str, size: int) -> float:
    fa, fc = F(MONO, size), F(CN, size)
    total = 0.0
    for ch in text:
        total += (fc if _is_cn(ch) else fa).getlength(ch)
    return total


def _is_cn(ch: str) -> bool:
    o = ord(ch)
    return o >= 0x2E80 or ch in "✓✓→←↑↓×"


def draw_console_text(d, x, y, text, size, fill):
    fa, fc = F(MONO, size), F(CN, size)
    cx = x
    for ch in text:
        fnt = fc if _is_cn(ch) else fa
        d.text((cx, y), ch, font=fnt, fill=fill)
        cx += fnt.getlength(ch)


def fig_console() -> Path:
    text = (RES / "run_log.txt").read_text(encoding="utf-8").rstrip("\n")
    lines = text.split("\n")
    # 只截取四个题目的运行结果（到“对照实验”之前），保持画面可读
    cut = [i for i, ln in enumerate(lines) if ln.startswith("[对照实验]")]
    if cut:
        lines = lines[: cut[0]]

    fs = 27
    line_h = int(fs * 1.45)
    pad = 26
    bar_h = 56
    maxw = max(_advance(ln, fs) for ln in lines)
    w = int(maxw) + 2 * pad
    h = bar_h + pad * 2 + line_h * len(lines)

    img = Image.new("RGB", (w, h), (30, 30, 32))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, bar_h], fill=(52, 53, 56))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 26 + i * 30
        d.ellipse([cx - 9, bar_h / 2 - 9, cx + 9, bar_h / 2 + 9], fill=col)
    draw_console_text(d, 130, bar_h / 2 - fs * 0.62, "Windows PowerShell  —  python -m src.run_all",
                      fs - 2, (200, 204, 210))

    y = bar_h + pad
    for ln in lines:
        color = (222, 226, 232)
        if "√" in ln:
            color = (130, 220, 150)
        if ln.startswith("==="):
            color = (255, 214, 120)
        if ln.startswith("["):
            color = (130, 190, 255)
        draw_console_text(d, pad, y, ln, fs, color)
        y += line_h

    out = FIG / "fig5_console.png"
    img.save(out, dpi=(200, 200))
    return out


def main() -> None:
    data = json.loads((RES / "results.json").read_text(encoding="utf-8"))
    print(fig_maze(data))
    print(fig_terrain(data))
    print(fig_nodes(data))
    print(fig_matrix(data))
    print(fig_console())


if __name__ == "__main__":
    main()
