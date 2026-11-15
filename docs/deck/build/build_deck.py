"""Build the Tiger Qubits pitch deck in the Tennessee Quantum Hackathon five-slide format.
Cover + 5 template slides, plus 3 hidden "see the grid" slides reached by a button."""
import re, sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

A = sys.argv[1]            # asset dir (scratchpad)
OUT = sys.argv[2]
PINK, CYAN, YEL = "FA3EC4", "8CF7F5", "FFE600"
INK, CARD, WHITE, MUTE = "1F2024", "F3F4F6", "FFFFFF", "50555C"
FONT = "Arial"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def rgb(h): return RGBColor.from_string(h)


def box(s, x, y, w, h, fill=None, shape=MSO_SHAPE.RECTANGLE, line=None, name=None):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill: sp.fill.solid(); sp.fill.fore_color.rgb = rgb(fill)
    else: sp.fill.background()
    if line: sp.line.color.rgb = rgb(line); sp.line.width = Pt(1.5)
    else: sp.line.fill.background()
    sp.shadow.inherit = False
    if name: sp.name = name
    return sp


def text(s, x, y, w, h, runs, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    """runs: str or list of paragraphs; a paragraph is str or (str, dict(size,bold,color))."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = runs if isinstance(runs, list) else [runs]
    for i, p in enumerate(paras):
        t, o = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        if spacing is not None or "space" in o: para.space_before = Pt(o.get("space", spacing or 0))
        r = para.add_run(); r.text = t
        f = r.font; f.name = FONT; f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold)
        f.color.rgb = rgb(o.get("color", color))
    return tb


def pic(s, f, x, y, w=None, h=None, name=None):
    p = s.shapes.add_picture(f"{A}/{f}", Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    if name: p.name = name
    return p


FOOT = "QUANTUM HACKATHON  |  FIVE SLIDES • FIVE MINUTES"


def chrome(s, chip, chip_color, chip_w):
    pic(s, "star_small.png", 13.333 - 2.32, 0, w=2.32)
    pic(s, "footer_logos.png", 7.25, 6.4, w=5.3)
    text(s, 0.8, 6.95, 6, 0.25, FOOT, size=10, bold=True)
    box(s, 0.8, 0.8, chip_w, 0.42, chip_color)
    text(s, 0.94, 0.8, chip_w, 0.42, chip, size=12, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def title(s, t): text(s, 0.8, 1.35, 11.3, 1.1, t, size=44, bold=True)


# ---------------------------------------------------------------- cover
s0 = prs.slides.add_slide(BLANK)
pic(s0, "star_big.png", 13.333 - 4.32, 7.5 - 4.6, w=4.32)
pic(s0, "wordmark.png", 0.85, 0.8, w=4.9)
pic(s0, "partners.png", 7.75, 0.6, w=4.85)
box(s0, 0.8, 3.35, 4.2, 0.45, CYAN)
text(s0, 0.9, 3.35, 4.0, 0.45, "POWER GRID TRACK", size=14, bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s0, 0.85, 4.1, 7.5, 0.9, "Tiger Qubits", size=54, bold=True)
text(s0, 0.9, 5.2, 7.2, 0.9, "Grid Monitoring: Optimized", size=26)
text(s0, 0.9, 6.0, 7.2, 0.4, "Where should a power company put its grid sensors, and can a quantum computer help decide?", size=14, color=MUTE)
text(s0, 0.9, 6.75, 7, 0.5, "Tennessee Quantum Hackathon  ·  November 13–15, 2026", size=14, bold=True)

# ---------------------------------------------------------------- 1 problem
s1 = prs.slides.add_slide(BLANK)
chrome(s1, "01 / THE PROBLEM", PINK, 2.45)
title(s1, "What problem are we solving?")
cards = [
    ("1", "Where do sensors go?", "A utility must see every substation live, using as few sensors (PMUs) as possible. We solve this on the 14-substation IEEE test grid."),
    ("2", "Why does it matter?", "Each PMU costs $40k–$180k to install. Fewer sensors save money, but each one that fails leaves substations blind."),
    ("3", "What is inadequate?", "The textbook answer is 4 sensors: cheapest and most fragile. Lose the one at bus 6 and 4 substations go dark. Seeing every bus twice takes 9."),
]
for i, (n, h, b) in enumerate(cards):
    x = 0.8 + i * 4.03
    box(s1, x, 2.85, 3.68, 3.35, CARD)
    box(s1, x + 0.3, 3.1, 0.62, 0.62, PINK)
    text(s1, x + 0.3, 3.1, 0.62, 0.62, n, size=22, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s1, x + 0.3, 3.95, 3.1, 0.7, h, size=20, bold=True)
    text(s1, x + 0.3, 4.65, 3.1, 1.5, b, size=14, color=MUTE)
btn_see = box(s1, 0.8, 6.38, 2.9, 0.42, None, MSO_SHAPE.ROUNDED_RECTANGLE, line=INK, name="btn see the grid")
text(s1, 0.8, 6.38, 2.9, 0.42, "►  See the grid in 3D", size=12, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 2 who
s2 = prs.slides.add_slide(BLANK)
chrome(s2, "02 / IDEAL CUSTOMER PROFILE", CYAN, 3.65)
title(s2, "Who needs this solution?")
box(s2, 0.8, 2.8, 5.78, 2.35, CARD); box(s2, 6.69, 2.8, 5.84, 2.35, CARD)
text(s2, 1.2, 3.1, 5, 0.3, "WHO BUYS", size=13, bold=True)
text(s2, 1.2, 3.55, 5.1, 1.5, [("Power utilities", dict(size=26, bold=True)),
     ("TVA first. Also grid software vendors and engineering consultants who plan for utilities.", dict(size=14, color=MUTE, space=8))])
text(s2, 7.1, 3.1, 5, 0.3, "WHO USES IT", size=13, bold=True)
text(s2, 7.1, 3.55, 5.2, 1.5, [("Grid planning engineers", dict(size=26, bold=True)),
     ("The planning lead who owns the sensor budget signs off.", dict(size=14, color=MUTE, space=8))])
box(s2, 0.8, 5.25, 11.73, 1.05, INK)
text(s2, 1.2, 5.25, 2.6, 1.05, "WHY THEY’D SAY YES", size=13, bold=True, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
text(s2, 3.9, 5.25, 8.4, 1.05, "A placement they can verify, cost versus backup priced up front, and an honest answer on whether quantum is worth paying for.", size=16, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 3 build
s3 = prs.slides.add_slide(BLANK)
chrome(s3, "03 / SOLUTION & TECHNOLOGY", YEL, 3.5)
title(s3, "What did we build?")
steps = [
    ("STEP 1  ·  METHOD", "A quantum search", "Each substation is a yes/no: sensor or not. QAOA (5 layers, penalty 2, CVaR α = 0.25) tries many combinations at once and favors the good ones.", YEL),
    ("STEP 2  ·  BUILD", "Shrink, split, repair", "Shrink the grid, split it into pieces, search each, repair. A checker proves every substation is covered. Result: sensors at buses 2, 6, 7, 9.", CARD),
    ("STEP 3  ·  STATUS", "Runs on real chips", "Works on simulators and two quantum chips (Rigetti, IonQ). Unproven: any win over the classical exact solver.", CARD),
]
for i, (k, h, b, fill) in enumerate(steps):
    x = 0.8 + i * 4.14
    box(s3, x, 2.72, 3.45, 3.45, fill)
    text(s3, x + 0.35, 3.0, 2.9, 0.3, k, size=12, bold=True)
    text(s3, x + 0.35, 3.45, 2.8, 0.8, h, size=20, bold=True)
    text(s3, x + 0.35, 4.2, 2.8, 1.9, b, size=15, color=INK if fill == YEL else MUTE)
    if i < 2: text(s3, x + 3.5, 4.1, 0.6, 0.6, "→", size=30, bold=True, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 4 team
s4 = prs.slides.add_slide(BLANK)
chrome(s4, "04 / THE TEAM", CYAN, 2.2)
title(s4, "Who made it happen?")
team = [("TM", "Theopolis MaCnificent", CYAN), ("JM", "Jordan Milsap", PINK), ("JP", "Jennifer Pirkle", YEL),
        ("MM", "Maalik Matthews", CYAN), ("DA", "Donnie Apple", PINK)]
for i, (ini, nm, col) in enumerate(team):
    x = 0.8 + i * 2.4
    box(s4, x, 2.52, 2.15, 3.4, CARD)
    box(s4, x + 0.3, 2.8, 0.95, 0.95, col, MSO_SHAPE.OVAL)
    text(s4, x + 0.3, 2.8, 0.95, 0.95, ini, size=22, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s4, x + 0.3, 3.95, 1.75, 0.8, nm, size=17, bold=True)
    text(s4, x + 0.3, 4.8, 1.75, 1.1, ["[Expertise]", "[What they built]"], size=13, color=MUTE)
text(s4, 0.9, 6.05, 5.8, 0.6, "Technical and commercial skills, one grid.", size=15, bold=True)

# ---------------------------------------------------------------- 5 learned
s5 = prs.slides.add_slide(BLANK)
chrome(s5, "05 / WHAT WE LEARNED", PINK, 2.75)
title(s5, "What changed in 36 hours?")
learn = [
    ("VALIDATED", "Classical works today", "The exact solver finds the true best answer for grids up to 300 substations in milliseconds. On real hardware, 43% of Rigetti runs were valid.", CYAN),
    ("SURPRISED US", "No quantum speedup", "Count the tuning cost fairly and random search catches up. Quantum has a signal, not a win.", PINK),
    ("NEXT", "Harder versions", "See every substation twice, weighted and budgeted, on bigger grids and better chips.", YEL),
]
for i, (k, h, b, fill) in enumerate(learn):
    x = 0.8 + i * 4.03
    box(s5, x, 2.7, 3.68, 3.5, fill)
    text(s5, x + 0.35, 2.98, 3.0, 0.3, k, size=13, bold=True)
    text(s5, x + 0.35, 3.45, 3.0, 0.8, h, size=22, bold=True)
    text(s5, x + 0.35, 4.5, 3.0, 1.7, b, size=14)

# ---------------------------------------------------------------- hidden demo slides
LABELS = ["3D city", "Grid only", "Sensors (PMUs)"]


def demo(idx, chip, head, desc, kind):
    s = prs.slides.add_slide(BLANK)
    s._element.set("show", "0")
    chrome(s, chip, PINK, 2.2)
    title(s, "See the grid")
    if kind == "video":
        pic(s, "frame3.png", 0.8, 2.55, w=7.4, h=4.16 - 0.0, name="poster")
    else:
        pic(s, kind, 0.8, 2.55, w=7.0, h=7.0 * 700 / 1200, name="map")
    text(s, 8.7, 2.7, 3.9, 1.0, head, size=24, bold=True)
    text(s, 8.7, 3.75, 3.9, 2.1, desc, size=14, color=MUTE)
    return s


slides_demo = []
cfg = [
    (0, "SEE IT", "The city, in 3D", "The IEEE 14 test grid as a city: 14 substations, 20 lines, and the 4 sensors in gold.", "video"),
    (1, "SEE IT", "Every substation, linked", "14 substations and 20 power lines. This is what the utility has to watch.", "grid.png"),
    (2, "SEE IT", "Four sensors see all fourteen", "Gold tags mark the 4 PMUs, at buses 2, 6, 7 and 9. If one fails, these go dark: bus 2 → 1, 2, 3. Bus 6 → 6, 11, 12, 13. Bus 7 → 8. Bus 9 → 10, 14.", "sensors.png"),
]
for c in cfg:
    slides_demo.append(demo(*c))

# buttons on demo slides (positioned under the map, row of 3 + back)
BTN_Y = 5.95
def add_buttons(s, active):
    out = []
    for i, l in enumerate(LABELS):
        on = i == active
        bx = 8.7 + (0 if i == 0 else 0)
        bx = 0.8 + i * 2.05
        sp = box(s, bx, 6.42, 1.9, 0.42, INK if on else WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, line=INK, name=f"btn {l}")
        text(s, bx, 6.42, 1.9, 0.42, l, size=12, bold=True, color=WHITE if on else INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        out.append(sp)
    back = box(s, 8.7, 5.8, 3.0, 0.42, None, MSO_SHAPE.ROUNDED_RECTANGLE, line=PINK, name="btn back")
    text(s, 8.7, 5.8, 3.0, 0.42, "←  Back to the deck", size=12, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return out, back

# map height is 4.08 (7.0*700/1200); video poster 4.16 -> map ends ~6.7. Move buttons so they don't cover it:
# shrink visuals a little first
for s, c in zip(slides_demo, cfg):
    for sh in s.shapes:
        if sh.name in ("map", "poster"):
            ratio = sh.height / sh.width
            sh.width = Inches(6.4); sh.height = Inches(6.4 * ratio)
for s, c in zip(slides_demo, cfg):
    s._btns, s._back = add_buttons(s, c[0])

# ---- links
for s in slides_demo:
    for sp, tgt in zip(s._btns, slides_demo):
        sp.click_action.target_slide = tgt
    s._back.click_action.target_slide = s1
btn_see.click_action.target_slide = slides_demo[0]

# ---- video on the 3D city slide
vs = slides_demo[0]
poster = [sh for sh in vs.shapes if sh.name == "poster"][0]
x, y, w, h = poster.left, poster.top, poster.width, poster.height
poster._element.getparent().remove(poster._element)
mv = vs.shapes.add_movie(f"{A}/city.mp4", x, y, w, h, poster_frame_image=f"{A}/frame3.png", mime_type="video/mp4")
mv.name = "scene"
vid_id = mv.shape_id
xml = mv._element.xml
# drop the media click action (it pauses the video and shows the control bar)
for el in mv._element.xpath(".//a:hlinkClick"):
    el.getparent().remove(el)
# transparent shield over the video so clicks never reach the player
shield = box(vs, x / 914400, y / 914400, w / 914400, h / 914400, WHITE, name="click-shield")
from lxml import etree
sf = shield._element.xpath(".//a:solidFill/a:srgbClr")[0]
etree.SubElement(sf, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha").set("val", "0")
TIMING = open(f"{A}/timing.xml").read().replace('spid="2"', f'spid="{vid_id}"').replace("<p:timing>", '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">',1)
vs._element.append(etree.fromstring(TIMING))
# keep the shield above the video but below the buttons: move video first among shapes
tree = vs.shapes._spTree
tree.remove(mv._element); tree.insert(2, mv._element)

prs.save(OUT)
print("saved", OUT)
