import sys, math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONT = sys.argv[1]; OUT = sys.argv[2]
f = TTFont(FONT); gs = f.getGlyphSet(); cmap = f.getBestCmap()
upm = f['head'].unitsPerEm; cap = f['OS/2'].sCapHeight or 700

def text_path(txt, cap_h, tracking_em, x0=0, y_base=0):
    """Outline text as one SVG path; returns (d, width)."""
    s = cap_h / cap; x = 0; pen = SVGPathPen(gs)
    for ch in txt:
        if ch == ' ':
            x += gs[cmap[32]].width * s + tracking_em * cap_h; continue
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, x0 + x, y_base))
        gs[g].draw(tp)
        x += gs[g].width * s + tracking_em * cap_h
    return pen.getCommands(), x - tracking_em * cap_h

# ---- mark: P = stem with keel cut + flanged porthole ring ----
def mark(fill, uid):
    cx, cy, R, r = 56, 38, 30, 16
    bolts = "".join(f'<circle cx="{cx+23*math.cos(a):.2f}" cy="{cy+23*math.sin(a):.2f}" r="2.1" fill="#000"/>'
                    for a in [i*math.pi/4 + math.pi/8 for i in range(8)])
    return f'''<mask id="m{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">
      <rect width="100" height="100" fill="#fff"/>{bolts}
      <rect x="0" y="72" width="100" height="3" fill="#000"/>
    </mask>
    <g mask="url(#m{uid})" fill="{fill}">
      <path fill-rule="evenodd" d="M{cx-R},{cy} a{R},{R} 0 1 0 {2*R},0 a{R},{R} 0 1 0 {-2*R},0 Z M{cx-r},{cy} a{r},{r} 0 1 1 {2*r},0 a{r},{r} 0 1 1 {-2*r},0 Z"/>
      <polygon points="18,8 34,8 34,80 18,94"/>
    </g>
    <circle cx="{cx}" cy="{cy}" r="11" fill="none" stroke="{fill}" stroke-width="1.6"/>'''

STEEL = '''<linearGradient id="steel" gradientUnits="userSpaceOnUse" x1="10" y1="0" x2="95" y2="100">
      <stop offset="0" stop-color="#5d666f"/><stop offset=".28" stop-color="#e9edf0"/>
      <stop offset=".5" stop-color="#7c868f"/><stop offset=".72" stop-color="#d3d9de"/>
      <stop offset="1" stop-color="#4f575f"/></linearGradient>'''

def svg(vb, inner, bg=None, scale=3, defs=""):
    w, h = vb[2], vb[3]
    rect = f'<rect x="{vb[0]}" y="{vb[1]}" width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(f"{v:g}" for v in vb)}" width="{w*scale:g}" height="{h*scale:g}" role="img" aria-label="Petrichor">
  <title>Petrichor</title>
  <defs>{defs}</defs>
  {rect}
  {inner}
</svg>
'''

word_d, word_w = text_path("PETRICHOR", 30, 0.28)
tag_d, tag_w = text_path("MARINE STAINLESS · CROATIA", 7.2, 0.62)

def lockup_h(ink, sub, markfill, uid):
    # mark 100 tall; wordmark cap 30 centred-ish, tagline under it
    x = 128
    return (f'{mark(markfill, uid)}'
            f'<path transform="translate({x} 53)" d="{word_d}" fill="{ink}"/>'
            f'<path transform="translate({x+1} 77)" d="{tag_d}" fill="{sub}"/>'), x + max(word_w, tag_w)

def lockup_v(ink, sub, markfill, uid):
    W = max(word_w, tag_w); mx = W/2 - 50
    return (f'<g transform="translate({mx:.2f} 0)">{mark(markfill, uid)}</g>'
            f'<path transform="translate({(W-word_w)/2:.2f} 146)" d="{word_d}" fill="{ink}"/>'
            f'<path transform="translate({(W-tag_w)/2:.2f} 172)" d="{tag_d}" fill="{sub}"/>'), W

INK, SUB, LIGHT, LSUB, DARK = "#14191e", "#6b747c", "#eef1f3", "#8e979f", "#0d1114"
os.makedirs(OUT, exist_ok=True)
out = {}
for name, ink, sub, mf, bg in [("", INK, SUB, INK, None), ("-white", LIGHT, LSUB, LIGHT, None),
                               ("-steel", INK, SUB, "url(#steel)", None), ("-steel-dark", LIGHT, LSUB, "url(#steel)", DARK)]:
    inner, W = lockup_h(ink, sub, mf, "h")
    out[f"petrichor-logo{name}.svg"] = svg((-10, -10, W + 20, 120), inner, bg, defs=STEEL if "steel" in mf else "")
    inner, W = lockup_v(ink, sub, mf, "v")
    out[f"petrichor-logo-stacked{name}.svg"] = svg((-16, -14, W + 32, 206), inner, bg, defs=STEEL if "steel" in mf else "")
for name, mf, bg in [("", INK, None), ("-white", LIGHT, None), ("-steel", "url(#steel)", None), ("-app-icon", "url(#steel)", DARK)]:
    out[f"petrichor-mark{name}.svg"] = svg((-8, -6, 116, 116) if bg else (0, 0, 100, 100), mark(mf, "k"), bg, defs=STEEL if "steel" in mf else "")
for n, s in out.items(): open(os.path.join(OUT, n), "w").write(s)
print("word", round(word_w,1), "tag", round(tag_w,1), len(out), "files")
