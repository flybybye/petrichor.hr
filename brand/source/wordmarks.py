import sys, os
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FD, OUT = sys.argv[1], sys.argv[2]
# (key, label, file, axes, word tracking, tagline axes, tag tracking)
OPTS = [
 ("A-michroma",  "A · Michroma",            "Michroma-Regular.ttf", None,                       .28, None,          .62),
 ("B-syncopate", "B · Syncopate Bold",      "Syncopate.ttf",        None,                       .22, None,          .55),
 ("C-archivo",   "C · Archivo Expanded",    "Archivo.ttf",          {"wdth":125,"wght":650},    .16, {"wdth":125,"wght":450}, .55),
 ("D-josefin",   "D · Josefin Sans",        "JosefinSans.ttf",      {"wght":300},               .42, {"wght":400},   .6),
 ("E-cinzel",    "E · Cinzel",              "Cinzel.ttf",           {"wght":500},               .30, {"wght":500},   .55),
 ("F-unbounded", "F · Unbounded",           "Unbounded.ttf",        {"wght":500},               .14, {"wght":400},   .5),
 ("G-grotesk",   "G · Space Grotesk",       "SpaceGrotesk.ttf",     {"wght":500},               .30, {"wght":400},   .55),
]
TAG = "MARINE STAINLESS · CROATIA"
CAP, TCAP, GAP = 30, 7, 20

def load(fn, axes):
    f = TTFont(os.path.join(FD, fn))
    if axes and "fvar" in f: f = instantiateVariableFont(f, axes)
    return f

def outline(f, txt, cap_h, track):
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    capu = getattr(f["OS/2"], "sCapHeight", 0) or 700
    # measure real cap height from H for accuracy
    bp = BoundsPen(gs); gs[cmap[ord("H")]].draw(bp); capu = bp.bounds[3]
    s = cap_h / capu; x = 0; pen = SVGPathPen(gs)
    for ch in txt:
        g = gs[cmap[ord(ch)]]
        if ch != " ": g.draw(TransformPen(pen, (s, 0, 0, -s, x, 0)))
        x += g.width * s + track * cap_h
    return pen.getCommands(), x - track * cap_h

def svg(vb, inner, bg=None):
    rect = f'<rect x="{vb[0]:g}" y="{vb[1]:g}" width="{vb[2]:g}" height="{vb[3]:g}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(f"{v:.1f}" for v in vb)}" '
            f'width="{vb[2]*3:.0f}" height="{vb[3]*3:.0f}" role="img" aria-label="Petrichor"><title>Petrichor</title>{rect}{inner}</svg>\n')

INK, SUB, LIGHT, LSUB, DARK = "#14191e", "#6b747c", "#eef1f3", "#8e979f", "#0d1114"
os.makedirs(OUT, exist_ok=True)
sheet, sy, SW = [], 0, 0
built = []
for key, label, fn, ax, tr, tax, ttr in OPTS:
    wd, ww = outline(load(fn, ax), "PETRICHOR", CAP, tr)
    td, tw = outline(load(fn, tax), TAG, TCAP, ttr)
    W = max(ww, tw)
    def inner(ink, sub, ox=0, oy=0, wd=wd, td=td, W=W, ww=ww, tw=tw):
        return (f'<path transform="translate({ox+(W-ww)/2:.2f} {oy+CAP:.2f})" d="{wd}" fill="{ink}"/>'
                f'<path transform="translate({ox+(W-tw)/2:.2f} {oy+CAP+GAP+TCAP:.2f})" d="{td}" fill="{sub}"/>')
    H = CAP + GAP + TCAP
    vb = (-14, -14, W + 28, H + 28)
    for suf, ink, sub, bg in [("", INK, SUB, None), ("-white", LIGHT, LSUB, None), ("-preview-dark", LIGHT, LSUB, DARK), ("-preview", INK, SUB, "#ffffff")]:
        open(os.path.join(OUT, f"petrichor-{key}{suf}.svg"), "w").write(svg(vb, inner(ink, sub), bg))
    # word only (no tagline)
    open(os.path.join(OUT, f"petrichor-{key}-word.svg"), "w").write(
        svg((-8, -8, ww + 16, CAP + 16), f'<path transform="translate(0 {CAP})" d="{wd}" fill="{INK}"/>'))
    built.append((label, W, inner))
    SW = max(SW, W)

# comparison sheet: light column left, dark column right
ROW, PAD, LBL = 110, 40, 16
cw = SW + 2 * PAD
parts = []
for i, (label, W, inner) in enumerate(built):
    y = i * ROW
    parts.append(f'<rect x="0" y="{y}" width="{cw}" height="{ROW}" fill="#ffffff"/><rect x="{cw}" y="{y}" width="{cw}" height="{ROW}" fill="{DARK}"/>')
    parts.append(f'<line x1="0" y1="{y}" x2="{2*cw}" y2="{y}" stroke="#d7dbde" stroke-width=".6"/>')
    parts.append(f'<text x="14" y="{y+LBL+4}" font-family="Helvetica, Arial" font-size="10" fill="#8a9298">{label}</text>')
    oy = y + (ROW - (CAP + GAP + TCAP)) / 2 + 6
    parts.append(inner(INK, SUB, (cw - W) / 2, oy))
    parts.append(inner(LIGHT, LSUB, cw + (cw - W) / 2, oy))
H = ROW * len(built)
open(os.path.join(OUT, "_usporedba.svg"), "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {2*cw:.0f} {H}" width="{4*cw:.0f}" height="{2*H}">{"".join(parts)}</svg>\n')
print("ok", len(built))
