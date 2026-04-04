import re, sys, os

# ── config ────────────────────────────────────────────────────────────────────

SVG_FILE  = "image.svg"
OUT_FILE  = "index.html"
BG        = "#e8e4dc"
COPPER    = "#c47a3a"

SVG_LAYERS = ["screen", "laptop", "keyboard", "me",
              "desk", "mat", "mouse", "mug", "chair", "chair2"]

TRANSFORMS = {
    "desk":     (0,       0),
    "screen":   (53.67,  -26.83),
    "mat":      (-49.19, -24.6),
    "laptop":   (84.97,   42.49),
    "keyboard": (-49.19, -24.6),
    "mouse":    (49.19,   24.6),
    "mug":      (-80.5,  -40.25),
    "chair":    (-35.78,  17.89),
    "me":       (-35.78,  17.89),
    "chair2":   (-35.78,  17.89),
}

LABELS = {
    "screen":   dict(name="LG 40WP95C-W",        sub=None,             x1=660, y1=220, x2=730, y2=195, tx=735, ty=199, anchor="start", kind="product"),
    "laptop":   dict(name="ThinkPad X1 Carbon",   sub='14"',            x1=690, y1=450, x2=760, y2=470, tx=765, ty=474, anchor="start", kind="product"),
    "keyboard": dict(name="Logitech K950 Slim",   sub=None,             x1=310, y1=315, x2=230, y2=295, tx=225, ty=299, anchor="end",   kind="product"),
    "mouse":    dict(name="Logitech Lift",         sub="Vertical Mouse", x1=530, y1=400, x2=610, y2=375, tx=615, ty=379, anchor="start", kind="product"),
    "mug":      dict(name="Coffee",               sub=None,             x1=310, y1=230, x2=225, y2=205, tx=220, ty=209, anchor="end",   kind="product"),
    "chair":    dict(name="HÅG Capisco",          sub=None,             x1=155, y1=640, x2=80,  y2=610, tx=75,  ty=614, anchor="end",   kind="product"),
    "me":       dict(name="ABOUT ME",             sub=None,             x1=None,y1=None,x2=None,y2=None,tx=175, ty=510, anchor="end",   kind="about"),
}

HIT_AREAS = {
    "screen":   (460, 80,  310, 320),
    "laptop":   (530, 360, 220, 160),
    "keyboard": (155, 240, 240, 130),
    "mouse":    (440, 360, 120, 100),
    "mug":      (255, 130, 110, 120),
    "chair":    (80,  580, 280, 260),
    "me":       (195, 490, 180, 140),
}

LAYER_ORDER = ["desk", "screen", "mat", "laptop", "keyboard",
               "mouse", "mug", "chair", "me", "chair2"]

# ── helpers ───────────────────────────────────────────────────────────────────

def extract_layer(source, layer_id):
    start_tag = f'<g id="{layer_id}"'
    start_idx = source.find(start_tag)
    if start_idx == -1: return None
    pos = source.find('>', start_idx) + 1
    depth = 1; end_idx = pos
    while depth > 0 and pos < len(source):
        no = source.find('<g', pos); nc = source.find('</g>', pos)
        if nc == -1: break
        if no != -1 and no < nc: depth += 1; pos = no + 2
        else:
            depth -= 1
            if depth == 0: end_idx = nc + 4
            pos = nc + 4
    opening = source[start_idx:source.find('>', start_idx)+1]
    return opening + source[source.find('>', start_idx)+1:end_idx]

# ── read SVG ──────────────────────────────────────────────────────────────────

if not os.path.exists(SVG_FILE):
    print(f"ERROR: {SVG_FILE} not found.")
    sys.exit(1)

with open(SVG_FILE) as f:
    svg = f.read()

defs_match = re.search(r'<defs>(.*?)</defs>', svg, re.DOTALL)
svg_defs = defs_match.group(1) if defs_match else ''

layers = {}
for lid in SVG_LAYERS:
    r = extract_layer(svg, lid)
    if r: layers[lid] = r; print(f"  ✓ {lid}")
    else: print(f"  ✗ {lid} — not found (skipping)")

# ── assemble pieces ───────────────────────────────────────────────────────────

css_transforms = "\n".join(
    f"  .svg-wrapper:hover .layer-{l} {{ transform: translate({tx}px, {ty}px); }}"
    for l, (tx, ty) in TRANSFORMS.items()
)

html_layers = ""
for l in LAYER_ORDER:
    if l not in layers: continue
    inner = layers[l]
    inner = re.sub(f'<g id="{l}"[^>]*>', f'<g id="{l}" class="layer-group layer-{l}">', inner, count=1)
    html_layers += "      " + inner + "\n"

html_hits = "".join(
    f'      <rect class="hit-area" data-layer="{l}" x="{x}" y="{y}" width="{w}" height="{h}"/>\n'
    for l, (x, y, w, h) in HIT_AREAS.items()
)

html_labels = ""
for l, cfg in LABELS.items():
    kind, name, sub = cfg["kind"], cfg["name"], cfg.get("sub")
    x1, y1, x2, y2 = cfg["x1"], cfg["y1"], cfg["x2"], cfg["y2"]
    tx, ty, anchor = cfg["tx"], cfg["ty"], cfg["anchor"]
    sub_dy = ty + 14
    copied_y = sub_dy + 13 if sub else ty + 13
    dot = f'<circle class="label-dot" cx="{x1}" cy="{y1}" r="2.5"/>' if kind=="product" and x1 else ""
    line = f'<line class="label-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>' if kind=="product" and x1 else ""
    subtext = f'<text class="label-sub" x="{tx}" y="{sub_dy}" text-anchor="{anchor}">{sub}</text>' if sub else ""
    html_labels += f"""
        <g class="label-group" id="label-{l}" data-layer="{l}" data-kind="{kind}" data-name="{name}">
          {dot}{line}
          <text class="label-name is-{kind}" x="{tx}" y="{ty}" text-anchor="{anchor}">{name}</text>
          {subtext}
          <text class="copied-text" x="{tx}" y="{copied_y}" text-anchor="{anchor}" id="copied-{l}">copied</text>
        </g>"""

js_transforms = "\n".join(
    f'  {l}: [{tx}, {ty}],'
    for l, (tx, ty) in TRANSFORMS.items() if l in LABELS
)

# ── write HTML ────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Desk</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: {BG};
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Inter', sans-serif;
    overflow: hidden;
  }}
  .container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.25rem;
    padding: 2rem;
  }}
  .title {{
    font-size: 0.65rem;
    font-weight: 300;
    color: #aaa;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    opacity: 0;
    animation: fadeUp 0.8s ease 0.4s forwards;
  }}
  .hint {{
    font-size: 0.6rem;
    font-weight: 300;
    color: #bbb;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    transition: opacity 0.6s;
    opacity: 0;
    animation: fadeUp 0.8s ease 0.6s forwards;
  }}
  .svg-wrapper:hover ~ .hint {{ opacity: 0 !important; animation: none; }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  /* page enter — zoom out from inside the screen */
  .svg-wrapper {{
    position: relative;
    width: min(90vw, 680px);
    height: min(90vw, 680px);
    cursor: crosshair;
    transform-origin: 62% 30%;
    animation: zoomOut 0.75s cubic-bezier(0.2, 0, 0.3, 1) forwards;
  }}
  @keyframes zoomOut {{
    from {{ transform: scale(10); opacity: 0; }}
    to   {{ transform: scale(1);  opacity: 1; }}
  }}

  .svg-wrapper svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}
  .layer-group {{
    transition: transform 0.7s cubic-bezier(0.34, 1.4, 0.64, 1);
  }}
{css_transforms}

  .hit-area {{ fill: transparent; stroke: none; cursor: pointer; }}
  .hit-area[data-layer="screen"] {{ cursor: zoom-in; }}

  .label-group {{
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s ease;
  }}
  .label-group.visible {{ opacity: 1; }}
  .label-line {{
    stroke: {COPPER};
    stroke-width: 0.8;
    fill: none;
    stroke-dasharray: 300;
    stroke-dashoffset: 300;
    transition: stroke-dashoffset 0.4s ease 0.05s;
    marker-end: url(#arrowhead);
  }}
  .label-group.visible .label-line {{ stroke-dashoffset: 0; }}
  .label-dot {{ fill: {COPPER}; }}
  .label-name {{
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 400;
    fill: #2d2620;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  .label-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 300;
    fill: #a08060;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}
  .label-name.is-about {{
    font-size: 13px;
    font-weight: 600;
    fill: {COPPER};
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
  }}
  .copied-text {{
    font-family: 'Inter', sans-serif;
    font-size: 9px;
    font-weight: 300;
    fill: {COPPER};
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0;
    transition: opacity 0.2s;
  }}
  .copied-text.show {{ opacity: 1; }}

  /* inception flash overlay */
  #flash {{
    position: fixed;
    inset: 0;
    background: {BG};
    opacity: 0;
    pointer-events: none;
    z-index: 999;
    transition: opacity 0.35s ease;
  }}
  #flash.show {{ opacity: 1; }}
</style>
</head>
<body>
<div id="flash"></div>
<div class="container">
  <span class="title">my desk</span>
  <div class="svg-wrapper" id="wrapper">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -80 1000 1000" id="main-svg">
      <defs>
        <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0.5 L5.5,3 L0,5.5" fill="none" stroke="{COPPER}" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round"/>
        </marker>
        {svg_defs}
      </defs>
{html_layers}
{html_hits}
      <g id="labels-root">
{html_labels}
      </g>
    </svg>
  </div>
  <span class="hint">hover to explore · click the screen</span>
</div>

<script>
const wrapper  = document.getElementById('wrapper');
const flash    = document.getElementById('flash');
let wrapperHovered = false;
let activeLayer    = null;

const layerTransforms = {{
{js_transforms}
}};

function positionLabels(hovered) {{
  document.querySelectorAll('.label-group').forEach(el => {{
    const t = layerTransforms[el.dataset.layer] || [0, 0];
    el.style.transform = hovered ? `translate(${{t[0]}}px, ${{t[1]}}px)` : 'translate(0,0)';
    el.style.transition = 'transform 0.7s cubic-bezier(0.34, 1.4, 0.64, 1)';
  }});
}}
function showLabel(id) {{
  if (activeLayer === id) return;
  hideAllLabels(); activeLayer = id;
  const el = document.getElementById('label-' + id);
  if (el) el.classList.add('visible');
}}
function hideAllLabels() {{
  document.querySelectorAll('.label-group').forEach(el => el.classList.remove('visible'));
  activeLayer = null;
}}

wrapper.addEventListener('mouseenter', () => {{ wrapperHovered = true;  positionLabels(true);  }});
wrapper.addEventListener('mouseleave', () => {{ wrapperHovered = false; positionLabels(false); hideAllLabels(); }});

document.querySelectorAll('.hit-area').forEach(el => {{
  el.addEventListener('mouseenter', () => {{ if (wrapperHovered) showLabel(el.dataset.layer); }});
  el.addEventListener('mouseleave', () => hideAllLabels());
}});

// ── inception: click screen ───────────────────────────────────────────────────
document.querySelector('.hit-area[data-layer="screen"]').addEventListener('click', () => {{
  // freeze hover state, stop animations
  wrapper.style.animation = 'none';
  wrapper.style.transition = 'transform 0.6s cubic-bezier(0.4, 0, 1, 1), opacity 0.45s ease 0.2s';
  wrapper.style.transformOrigin = '62% 30%'; // toward screen center
  wrapper.style.transform = 'scale(10)';
  wrapper.style.opacity   = '0';

  // flash to bg color then reload
  setTimeout(() => flash.classList.add('show'), 380);
  setTimeout(() => window.location.reload(), 700);
}});

// ── label click handlers ──────────────────────────────────────────────────────
document.querySelectorAll('.label-group').forEach(label => {{
  const {{ kind, name, layer: lid }} = label.dataset;
  if (kind === 'product') {{
    label.style.cursor = 'pointer';
    label.addEventListener('click', () => {{
      navigator.clipboard.writeText(name).then(() => {{
        const f = document.getElementById('copied-' + lid);
        if (f) {{ f.classList.add('show'); setTimeout(() => f.classList.remove('show'), 1400); }}
      }});
    }});
  }} else if (kind === 'about') {{
    label.style.cursor = 'pointer';
    label.addEventListener('click', () => window.location.href = 'about.html');
  }}
}});
</script>
</body>
</html>"""

with open(OUT_FILE, "w") as f:
    f.write(html)

print(f"\n✓ Built {OUT_FILE} ({len(html):,} bytes)")