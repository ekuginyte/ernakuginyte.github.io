import re, math, sys, os

# ── config ────────────────────────────────────────────────────────────────────

SVG_FILE   = "image.svg"          # your drawing — update whenever you export
OUT_FILE   = "index.html"         # output page
BG_COLOR   = "#e8e4dc"
COPPER     = "#c47a3a"

# Which layers exist in your SVG (update if you rename/add layers in Illustrator)
SVG_LAYERS = ["screen", "laptop", "keyboard", "me",
              "desk", "mat", "mouse", "mug", "chair", "chair2"]

# Explosion transforms (tx, ty) in SVG units — tweak freely
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

# Labels — edit name/sub/positions here
# x1,y1 = dot on the piece   x2,y2 = arrowhead end   tx,ty = text position
# anchor: "start" (text goes right) or "end" (text goes left)
# kind: "product" (copies name on click) or "about" (links to about.html)
LABELS = {
    "screen":   dict(name="LG 40WP95C-W",        sub=None,             x1=660, y1=220, x2=730, y2=195, tx=735, ty=199, anchor="start", kind="product"),
    "laptop":   dict(name="ThinkPad X1 Carbon",   sub='14"',            x1=690, y1=450, x2=760, y2=470, tx=765, ty=474, anchor="start", kind="product"),
    "keyboard": dict(name="Logitech K950 Slim",   sub=None,             x1=310, y1=315, x2=230, y2=295, tx=225, ty=299, anchor="end",   kind="product"),
    "mouse":    dict(name="Logitech Lift",         sub="Vertical Mouse", x1=530, y1=400, x2=610, y2=375, tx=615, ty=379, anchor="start", kind="product"),
    "mug":      dict(name="Coffee",               sub=None,             x1=310, y1=230, x2=225, y2=205, tx=220, ty=209, anchor="end",   kind="product"),
    "chair":    dict(name="HÅG Capisco",          sub=None,             x1=155, y1=640, x2=80,  y2=610, tx=75,  ty=614, anchor="end",   kind="product"),
    "me":       dict(name="ABOUT ME",             sub=None,             x1=None,y1=None,x2=None,y2=None,tx=175, ty=510, anchor="end",   kind="about"),
}
 
# Invisible hover areas
HIT_AREAS = {
    "screen":   (294, -5,  432, 412),
    "laptop":   (492, 303, 232, 210),
    "keyboard": (248, 276, 220, 145),
    "mouse":    (434, 381,  75,  56),
    "mug":      (307, 209,  77,  77),
    "chair":    (33,  386, 372, 462),
    "me":       (117, 253, 328, 439),
}

LAYER_ORDER = ["desk", "screen", "mat", "laptop", "keyboard",
               "mouse", "mug", "chair", "me", "chair2"]

# ── helpers ───────────────────────────────────────────────────────────────────

def extract_layer(source, layer_id):
    start_tag = f'<g id="{layer_id}"'
    start_idx = source.find(start_tag)
    if start_idx == -1:
        return None
    pos = source.find('>', start_idx) + 1
    depth = 1; end_idx = pos
    while depth > 0 and pos < len(source):
        no = source.find('<g', pos)
        nc = source.find('</g>', pos)
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
    print(f"ERROR: {SVG_FILE} not found. Make sure it's in the same folder as build.py")
    sys.exit(1)

with open(SVG_FILE) as f:
    svg = f.read()

defs_match = re.search(r'<defs>(.*?)</defs>', svg, re.DOTALL)
svg_defs = defs_match.group(1) if defs_match else ''

layers = {}
for layer_id in SVG_LAYERS:
    result = extract_layer(svg, layer_id)
    if result:
        layers[layer_id] = result
        print(f"  ✓ {layer_id}")
    else:
        print(f"  ✗ {layer_id} — not found in SVG (skipping)")

# ── build HTML ────────────────────────────────────────────────────────────────

def css_transforms():
    lines = []
    for layer, (tx, ty) in TRANSFORMS.items():
        lines.append(f"  .svg-wrapper:hover .layer-{layer} {{ transform: translate({tx}px, {ty}px); }}")
    return "\n".join(lines)

def label_js_transforms():
    relevant = {k: v for k, v in TRANSFORMS.items() if k in LABELS}
    lines = []
    for layer, (tx, ty) in relevant.items():
        lines.append(f'  {layer}: [{tx}, {ty}],')
    return "\n".join(lines)

html_layers = ""
for layer in LAYER_ORDER:
    if layer not in layers:
        continue
    inner = layers[layer]
    inner = re.sub(f'<g id="{layer}"[^>]*>', f'<g id="{layer}" class="layer-group layer-{layer}">', inner, count=1)
    html_layers += "      " + inner + "\n"

html_hits = ""
for layer, (x, y, w, h) in HIT_AREAS.items():
    html_hits += f'      <rect class="hit-area" data-layer="{layer}" x="{x}" y="{y}" width="{w}" height="{h}"/>\n'

html_labels = ""
for layer, cfg in LABELS.items():
    kind   = cfg["kind"]
    name   = cfg["name"]
    sub    = cfg.get("sub")
    x1, y1 = cfg["x1"], cfg["y1"]
    x2, y2 = cfg["x2"], cfg["y2"]
    tx, ty  = cfg["tx"], cfg["ty"]
    anchor  = cfg["anchor"]
    sub_dy  = ty + 14
    copied_y = sub_dy + 13 if sub else ty + 13

    dot_html = line_html = ""
    if kind == "product" and x1 is not None:
        dot_html  = f'<circle class="label-dot" cx="{x1}" cy="{y1}" r="2.5"/>'
        line_html = f'<line class="label-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'

    sub_html = f'<text class="label-sub" x="{tx}" y="{sub_dy}" text-anchor="{anchor}">{sub}</text>' if sub else ""

    html_labels += f"""
        <g class="label-group" id="label-{layer}" data-layer="{layer}" data-kind="{kind}" data-name="{name}">
          {dot_html}
          {line_html}
          <text class="label-name is-{kind}" x="{tx}" y="{ty}" text-anchor="{anchor}">{name}</text>
          {sub_html}
          <text class="copied-text" x="{tx}" y="{copied_y}" text-anchor="{anchor}" id="copied-{layer}">copied</text>
        </g>"""

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
    background: {BG_COLOR};
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    font-family: 'Inter', sans-serif;
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
  }}
  .hint {{
    font-size: 0.6rem;
    font-weight: 300;
    color: #bbb;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    transition: opacity 0.6s;
  }}
  .svg-wrapper:hover ~ .hint {{ opacity: 0; }}
  .svg-wrapper {{
    position: relative;
    width: min(90vw, 680px);
    height: min(90vw, 680px);
    cursor: crosshair;
  }}
  .svg-wrapper svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}
  .layer-group {{
    transition: transform 0.7s cubic-bezier(0.34, 1.4, 0.64, 1);
  }}
{css_transforms()}
  .hit-area {{ fill: transparent; stroke: none; cursor: pointer; }}
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
</style>
</head>
<body>
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
  <span class="hint">hover to explore</span>
</div>
<script>
const wrapper = document.getElementById('wrapper');
let wrapperHovered = false;
let activeLayer = null;
const layerTransforms = {{
{label_js_transforms()}
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
  hideAllLabels();
  activeLayer = id;
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
document.querySelectorAll('.label-group').forEach(label => {{
  const {{ kind, name, layer: layerId }} = label.dataset;
  if (kind === 'product') {{
    label.style.cursor = 'pointer';
    label.addEventListener('click', () => {{
      navigator.clipboard.writeText(name).then(() => {{
        const flash = document.getElementById('copied-' + layerId);
        if (flash) {{ flash.classList.add('show'); setTimeout(() => flash.classList.remove('show'), 1400); }}
      }});
    }});
  }} else if (kind === 'about') {{
    label.style.cursor = 'pointer';
    label.addEventListener('click', () => {{ window.location.href = 'about.html'; }});
  }}
}});
</script>
</body>
</html>"""

with open(OUT_FILE, "w") as f:
    f.write(html)

print(f"\n✓ Built {OUT_FILE} ({len(html):,} bytes)")