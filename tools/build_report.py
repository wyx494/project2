"""生成实验报告（docx），再由 LibreOffice 转成 PDF。

用法：
    python tools/build_report.py
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "report" / "figures"
OUT = ROOT / "report" / "实验二报告_搜索算法.docx"

SONG = "宋体"
HEI = "黑体"


def set_run_font(run, name: str, size: float, bold: bool = False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if color:
        run.font.color.rgb = RGBColor(*color)


def body(doc: Document, text: str, indent: bool = True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = 1.24
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    if indent:
        pf.first_line_indent = Pt(21)
    run = p.add_run(text)
    set_run_font(run, SONG, 10.5)
    return p


def heading(doc: Document, text: str):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(11)
    pf.space_after = Pt(5)
    pf.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, HEI, 12.5, bold=True)
    return p


def caption(doc: Document, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(8)
    run = p.add_run(text)
    set_run_font(run, SONG, 9, color=(90, 94, 100))
    return p


def picture(doc: Document, name: str, width_cm: float):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))


def shade(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(doc: Document, header, rows, widths):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        set_run_font(run, SONG, 9, bold=True)
        shade(cell, "EDEFF2")
    for row in rows:
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(text))
            set_run_font(run, SONG, 9)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
    return t


def add_hyperlink(paragraph, url: str, text: str, size: float = 9):
    """在段落里插入一个真正可点击的超链接。"""
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)

    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Consolas")
    fonts.set(qn("w:hAnsi"), "Consolas")
    fonts.set(qn("w:eastAsia"), SONG)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "2F6FD0")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    for el in (fonts, color, sz, underline):
        rPr.append(el)

    t = OxmlElement("w:t")
    t.text = text
    run.append(rPr)
    run.append(t)
    link.append(run)
    paragraph._p.append(link)
    return paragraph


def code_block(doc: Document, lines, size: float = 8.5):
    """等宽字体的浅灰底代码块，整体作为一个段落，保证底色连续。"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = Pt(size * 1.28)
    pf.space_before = Pt(3)
    pf.space_after = Pt(6)
    pf.left_indent = Cm(0.5)
    pf.right_indent = Cm(0.4)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F4F5F7")
    pPr.append(shd)
    borders = OxmlElement("w:pBdr")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "4")
        el.set(qn("w:color"), "DFE1E6")
        borders.append(el)
    pPr.append(borders)

    for i, line in enumerate(lines):
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(size)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), SONG)
        if i < len(lines) - 1:
            run.add_break()
    return p


def main() -> Path:
    data = json.loads((ROOT / "results" / "results.json").read_text(encoding="utf-8"))
    p1 = data["problem1"]
    p2 = data["problem2"]
    p3 = data["problem3"]
    p4 = data["problem4"]
    maze_rows = data["maze_rows"]

    doc = Document()

    # 页面：A4，常规页边距
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.1)
    sec.bottom_margin = Cm(2.1)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)

    normal = doc.styles["Normal"]
    normal.font.name = SONG
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), SONG)

    # ---------------------------------------------------------------- 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(6)
    title.paragraph_format.space_after = Pt(6)
    set_run_font(title.add_run("实验二　搜索算法实验报告"), HEI, 19, bold=True)

    repo = doc.add_paragraph()
    repo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    repo.paragraph_format.space_after = Pt(10)
    set_run_font(repo.add_run("代码仓库："), SONG, 9, color=(90, 94, 100))
    add_hyperlink(repo, "https://github.com/wyx494/project2",
                  "https://github.com/wyx494/project2", size=9)

    # ---------------------------------------------------------------- 一
    heading(doc, "一、实验目的与实现环境")
    body(doc, "这次实验要求把课上讲的两类搜索用自己的代码写出来：一类是带启发式的最优路径搜索 A*，"
              "另一类是对抗搜索里的 Minimax 与 Alpha-Beta 剪枝。四道题目是递进的，前两题只替换代价模型，"
              "第三题把场景换成博弈树，第四题再把两者拼在一起。")
    body(doc, "代码用 Python 3.12 写成，只依赖标准库，优先队列直接用 heapq 实现，没有引入任何搜索框架。"
              "四道题共用同一个 A* 函数，通过传入不同的“进入某格的代价”函数来区分无权迷宫和带权地形。"
              "所有输入输出都按实验指导给出的用例格式组织，运行 python -m src.run_all 会依次跑完四题并逐条打印与预期结果的比对。")

    # ---------------------------------------------------------------- 二
    heading(doc, "二、A* 的实现方式")
    body(doc, "我把 A* 写成一个通用函数 astar(grid, start, goal, entry_cost, weight)。状态就是格子坐标"
              "(row, col)；g 是从起点走到当前格已经付出的代价；h 取曼哈顿距离乘以权重 weight；f = g + h。"
              "开放表用二叉堆维护，堆元素是 (f, 入堆序号, 坐标)，加入序号是为了 f 相同时保持先进先出，"
              "避免同分节点在堆里反复比较；闭表记录已经扩展过的格子，弹出时若已在闭表就直接跳过。"
              "核心循环大致是这样（省掉了统计和返回值细节）：")
    code_block(doc, [
        "while open_heap:                                   # 队列非空",
        "    _, _, cur = heapq.heappop(open_heap)           # 弹出 f 最小的格子",
        "    if cur in closed: continue",
        "    closed.add(cur)                                # 计入扩展节点数",
        "    if cur == goal: return _reconstruct(came)      # 到达终点，回溯路径",
        "    for dr, dc in FOUR_DIRS:                       # 只走上下左右",
        "        nxt = (cur[0] + dr, cur[1] + dc)",
        "        if not passable(*nxt) or nxt in closed: continue",
        "        g_new = g_score[cur] + cost_of(*nxt)       # 进入该格的代价",
        "        if g_new < g_score.get(nxt, inf):          # 松弛，记录更优的 g",
        "            g_score[nxt], came[nxt] = g_new, cur",
        "            heapq.heappush(open_heap, (g_new + h(*nxt), counter, nxt))",
    ])
    body(doc, "代价统一在“进入某一格”时结算，起点格不计代价，所以题目一和题目二的差别只剩下 entry_cost 一个函数："
              "题目一每格恒为 1，题目二返回格子里的地形数字，终点 E 按指导规定返回 0。路径代价我还单独重算过一遍，"
              "与搜索中累计的 g 值一致。")
    body(doc, "选择曼哈顿距离是因为它同时满足可采纳性和一致性：网格上只能上下左右走，每步代价至少为 1，"
              "所以剩余步数不会少于两点的曼哈顿距离，h 不会高估真实代价；一致性（三角不等式）则保证节点第一次"
              "从堆里弹出时拿到的就是最优 g，闭表可以直接丢掉重复节点。这也是题目二讨论启发函数的前提。")

    # ---------------------------------------------------------------- 三
    heading(doc, "三、题目一：迷宫寻路")
    body(doc, "5×5 的迷宫直接用上面的函数求解，得到路径 (0,0)→(0,1)→(0,2)→(1,2)→(1,3)→(1,4)→(2,4)→(3,4)，"
              "一共 7 步，与预期输出一致。图 1 的第一幅画出了这条路径：先沿第一行向右，遇到障碍前折向第二行，"
              "再从右侧绕下来，走的是绕开中间那堵“墙”的最短路线。", align=WD_ALIGN_PARAGRAPH.LEFT)

    body(doc, "为了看清启发函数到底省了多少工作，我记录了搜索过程中真正从堆里弹出的格子数。用曼哈顿距离时扩展 "
              f"{int(p1['expanded'])} 个格子，把 h 置零（等价于按 g 排序，退化成一致代价搜索）则要扩展 "
              f"{int(p1['expanded_zero_h'])} 个，两者得到的路径完全相同。图 1 的中、右两幅把这批格子涂了色，"
              "可以看出 h=0 时搜索是向四周铺开的，连右下角那些明显背离终点的格子也被展开了；"
              "有启发值以后，堆顶始终偏向终点，很多“看着就不对”的方向根本没轮到。")
    picture(doc, "fig1_maze.png", 13.4)
    caption(doc, "图 1　题目一的最短路径（左），以及 h=0 与曼哈顿距离下实际被扩展的格子（中、右）")

    body(doc, "只有一张 5×5 的图，差别不够明显。我又用固定随机种子生成了四张更大、障碍率 28%–30% 的迷宫"
              "（保证起点到终点连通），规模从 10×10 一直到 25×25，统计结果见图 2。随着规模变大，两者的差距"
              f"从 1.3 倍扩大到 2.3 倍：25×25 时 h=0 要扩展 {int(maze_rows[-1]['zero'])} 个节点，"
              f"曼哈顿距离只要 {int(maze_rows[-1]['manhattan'])} 个。这和我事前的估计一致——"
              "启发函数的作用是把搜索从“均匀扩散”变成“朝目标收敛”，地图越大，扩散浪费的部分占比越高，"
              "启发值带来的收益也越明显。")
    picture(doc, "fig2_nodes.png", 12.9)
    caption(doc, "图 2　不同规模迷宫上两种启发函数的扩展节点数（同一随机种子，路径长度相同）")

    # ---------------------------------------------------------------- 四
    heading(doc, "四、题目二：加权地形")
    body(doc, "题目二把地图换成数字，进入一格的代价就是格中的数字。算法本身没有改动，只把 entry_cost 换成读取数字。"
              "从 (0,0) 出发，最优路线是先沿最左一列向下，再沿第 3 行向右，最后下到第 4 行抵达 E："
              "依次进入的格子代价都是 1，最后一步进入 E 按 0 计，总代价为 "
              f"{int(p2['cost'])}，与预期输出一致。图 3 把步序和到达每一格时的累计代价标在了格子的角上，"
              "可以看到代价是一格一格加上去的，中途没有出现 8 这样的大数，说明绕开高代价格的判断是对的。")

    body(doc, "这里有两处值得说明。一是终点的处理。指导里写明“最后一步没有代价，即可将 E 视为 0”，"
              "我最初按 1 算过一遍，得到 8，路线完全没变——这张图上终点代价只影响总代价的数值，不影响选路。"
              "但如果把终点也按 1 计，就等于在启发函数的假设里多加了一步，容易在多算的同时破坏 h 与真实代价"
              "之间的一致性，所以最终实现里对终点单独返回 0。")
    body(doc, "二是曼哈顿距离还能不能被采纳。我的结论是仍然可以，但前提是地形代价都不小于 1——这张图里最小代价"
              "正好是 1，每一步至少付 1，剩余步数依旧是真实代价的下界，h 不会高估。可采纳性保住了最优性，"
              "但 h 变得很“松”：它相当于假设后面每一步都走平原，一遇到沼泽就低估得厉害，于是搜索会往沼泽方向"
              f"多探一些。同一张图上 h=0 扩展了 {int(p2['expanded_zero_h'])} 个节点，用曼哈顿距离扩展 "
              f"{int(p2['expanded'])} 个，收益远小于题目一，原因就在这里。反过来说，如果地形代价允许小于 1"
              "（比如 0.5 的草地），曼哈顿就会高估，A* 也就不再保证最优，这时更稳妥的写法是“最小地形代价 × "
              "曼哈顿距离”作为下界。")
    picture(doc, "fig3_terrain.png", 9.0)
    caption(doc, "图 3　题目二的最优路径与累计代价（左上角数字为步序，右上角为累计代价）")

    # ---------------------------------------------------------------- 五
    heading(doc, "五、题目三：Minimax 与 Alpha-Beta")
    body(doc, "博弈树按指导的约定构造：根节点是 MAX，逐层交替，非叶子节点用 children 表示子节点，叶子节点用 value "
              "给分。Minimax 就是一次后序遍历，MAX 取子节点的最大值、MIN 取最小值，"
              f"整棵树 {int(p3['minimax_stats']['nodes'])} 个节点全部访问，根节点得到 {int(p3['minimax'])}。"
              "Alpha-Beta 在递归时多带两个界：MAX 节点用 alpha 记住自己已经能拿到的最好值，一旦某个子节点回传的"
              "值不小于 beta，就说明上一层 MIN 绝不会选这条路，后面的兄弟节点不必再看；MIN 节点对称处理。"
              "实现里我把剪枝判断放在更新 alpha/beta 之后，被剪掉的子树单独计数。")
    body(doc, f"对这棵示例树，Alpha-Beta 访问了 {int(p3['alpha_beta_stats']['nodes'])} 个节点、剪枝 "
              f"{int(p3['alpha_beta_stats']['prunes'])} 次，结果同样是 {int(p3['alpha_beta'])}。"
              "树太小，剪枝空间本来就有限，所以我另外用固定随机种子生了几棵更大的树做对比："
              "分支 4、深度 4 的树有 256 个叶子，Minimax 要访问 341 个节点，Alpha-Beta 只要 168 个，"
              "少了大约一半；分支 3、深度 4 时是 121 对 79。子节点顺序也有影响，把同一棵树的子节点反过来访问，"
              "剪枝次数就会变。这说明 Alpha-Beta 的实际效果依赖“好着法先出现”，真实对局里通常要先做一步"
              "启发式排序再开始搜索。")
    body(doc, "还有一个细节让我印象比较深：指导给的示例树里 max2 同时是 min1 和 min2 的子节点，"
              "也就是同一棵子树被两个父节点共用。第一次在 min1 下面访问它时，beta 已经被 max1 的 5 压住，"
              "max2 的第二个叶子 9 直接被剪掉；第二次在 min2 下面访问时 beta 是无穷大，9 又被完整算了出来。"
              "这提醒我，剪枝的依据是“当前搜索路径上的界”，而不是节点自身的值，同一棵子树在不同上下文里"
              "被剪与否可能完全不同。")

    # ---------------------------------------------------------------- 六
    heading(doc, "六、题目四：竞争环境下的宝藏分配")
    body(doc, "最后一题把 A* 和 Alpha-Beta 拼在一起。我先把 A、B、T1–T4 六个位置两两之间的最小移动代价都算出来，"
              "得到图 4 的 6×6 矩阵。地图上 A 和 B 分处左上角和右下角，四个宝藏散在四角，矩阵是对称的："
              "最远的是 A 到 B 的 12，最近的是 A 到 T2 的 4、B 到 T3 的 4。")
    picture(doc, "fig4_matrix.png", 8.9)
    caption(doc, "图 4　A* 求得的 6×6 最小移动代价矩阵（行是起点，列是目标）")

    body(doc, "博弈状态我设计成一个五元组：A 的位置、B 的位置、尚未被拿走的宝藏集合、双方的累计收益、当前轮到谁。"
              "每走一步，就按 Gain(p,Ti)=Vi−d(p,Ti) 结算收益并记到对应玩家名下；状态里不保存路径，"
              "因为题目只要求 A 的最优首步，需要路径时可以用 A* 重算。深度到 0 或宝藏被取完时结束，"
              "返回 Score_A−Score_B 作为评价值。A 层取最大值，B 层取最小值，与指导的设定一致。")
    table(doc,
          ["深度", "算法", "最优首步", "收益差", "访问节点", "剪枝次数"],
          [
              ["H = 2", "Minimax", p4["h2_minimax"]["best_target"], int(p4["h2_minimax"]["best_value"]),
               p4["h2_minimax"]["nodes"], p4["h2_minimax"]["prunes"]],
              ["H = 2", "Alpha-Beta", p4["h2_alpha-beta"]["best_target"], int(p4["h2_alpha-beta"]["best_value"]),
               p4["h2_alpha-beta"]["nodes"], p4["h2_alpha-beta"]["prunes"]],
              ["H = 4", "Minimax", "T3", int(p4["h4_minimax"]["best_value"]),
               p4["h4_minimax"]["nodes"], p4["h4_minimax"]["prunes"]],
              ["H = 4", "Alpha-Beta", p4["h4_alpha-beta"]["best_target"], int(p4["h4_alpha-beta"]["best_value"]),
               p4["h4_alpha-beta"]["nodes"], p4["h4_alpha-beta"]["prunes"]],
          ],
          [2.0, 3.0, 3.0, 2.6, 3.0, 2.8])
    caption(doc, "表 1　题目四在不同深度与算法下的搜索结果")

    body(doc, f"结果是 H=2 时 A 应取 T2、收益差 {int(p4['h2_alpha-beta']['best_value'])}，"
              f"H=4 时取 T3、收益差 {int(p4['h4_alpha-beta']['best_value'])}，与预期输出一致。"
              "两个深度的结论完全相反，这一点比数字本身更有意思。H=2 时搜索只能看到 A 走一步、B 走一步，"
              "A 拿 T2 之后 B 会立刻去拿最近、最划算的宝藏，A 的先手优势被抵消，最后差值是负的；"
              "深度加到 4 以后，搜索能看到 B 的反制之后 A 还有一次机会，T3 本身价值 7、离 A 有 8 步、"
              "离 B 只有 4 步，看上去是“A 拿不到的”，但它能改变第二轮的位置关系，让 A 后面占到 T1 或 T4，"
              "整条线路的净收益反而最高。这也说明限定深度的 Minimax 是在一棵被截断的树上作判断，"
              "深度不同，结论可能完全相反，不能只看一层就下结论。")
    body(doc, "搜索开销上，H=2 时两棵树都只有 16 个节点，Minimax 和 Alpha-Beta 没有差别，树太小根本剪不动；"
              "H=4 时 Minimax 要 64 个节点，Alpha-Beta 是 56 个、剪枝 11 次。我试着按即时收益从大到小排列子节点，"
              "节点数并没有继续下降，原因大概是这棵树的分支本来就只有 3 个、顺序也不算差，可剪的空间有限。")

    # ---------------------------------------------------------------- 七
    heading(doc, "七、运行结果与复现")
    body(doc, "图 5 是执行 python -m src.run_all 的终端输出，四道题的路径、代价、博弈结果和节点统计都在里面，"
              "每道题后面附了与预期输出的比对。README 里写了文件结构和运行方式，随机迷宫用固定种子生成，"
              "重复运行的结果不会变。")
    picture(doc, "fig5_console.png", 12.0)
    caption(doc, "图 5　程序运行结果（终端截图）")

    # ---------------------------------------------------------------- 八
    heading(doc, "八、小结与不足")
    body(doc, "这次实验最大的收获不是把三个算法写出来，而是看到了启发函数和访问顺序怎样具体地影响搜索开销："
              "同一个 A*，把 h 从 0 换成曼哈顿距离，25×25 迷宫上的扩展节点就少了一半；同一个 Alpha-Beta，"
              "换一下子节点的访问顺序，剪枝次数就会变化。过程中也踩了几个坑，比如终点代价该按 0 还是按 1、"
              "共享子树时 alpha/beta 怎样沿路径传递、限定深度会让最优首步发生反转，这些问题都是在对照实验里"
              "一个个暴露出来的。")
    body(doc, "代码还有可以改进的地方。题目四的状态里“双方位置 + 剩余宝藏”其实有很多重复，"
              "可以做成置换表缓存；子节点如果按估值排序，Alpha-Beta 的剪枝效率应该还能提高；"
              "题目二的启发函数也可以换成更紧的下界，看看扩展节点会不会继续下降。这些留到以后有时间再补。")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)
    return OUT


if __name__ == "__main__":
    main()
