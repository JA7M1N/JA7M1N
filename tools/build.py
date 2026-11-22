"""
Spider-Verse x frosted-glass GitHub profile builder.

    python tools/build.py            # rebuild every SVG in ./assets
    python tools/build.py --stats    # only refresh the live stats card

Pure SVG + CSS animation (no JS), so GitHub plays it inside the README.
Set GITHUB_TOKEN (or GH_TOKEN) to let the stats card pull live numbers.
"""
import base64
import datetime
import json
import os
import random
import sys
import urllib.request

# ----------------------------------------------------------------- CONFIG --
CONFIG = {
    "login": "JA7M1N",
    "name": "JAYMIN",
    "greeting": "HEY, I'M",
    "tagline": "your friendly neighborhood developer",
    "roles": ["building AI products", "shipping Flutter apps",
              "learning NeRF + 3D vision", "debugging at 2 a.m."],
    "status": "open to collabs",
    "id_rows": [
        ("NAME", "Jaymin"),
        ("ALIAS", "@JA7M1N"),
        ("UNIVERSE", "Earth-1610  /  the dev-verse"),
        ("POWERS", "Python · TypeScript · Flutter · AI"),
        ("CURRENTLY", "building AI tools for real problems"),
        ("STATUS", "open to collabs + internships"),
    ],
    "stack": [
        ("Python", "#3776ab"), ("TypeScript", "#3178c6"), ("JavaScript", "#f7df1e"),
        ("React", "#61dafb"), ("Next.js", "#ffffff"), ("Flutter", "#54c5f8"),
        ("Dart", "#00b4ab"), ("PyTorch", "#ee4c2c"), ("PHP", "#8892bf"),
        ("HTML", "#e34f26"), ("CSS", "#663399"), ("Git", "#f05032"),
    ],
    "projects": [
        ("CityPulse-AI", "CityPulse AI",
         "AI dashboard that predicts traffic, air pollution and waste so cities can act before problems hit.",
         "TypeScript", "#3178c6"),
        ("Secure-AI", "Secure AI",
         "Web platform that spots phishing, fraud and privacy risks with AI and shows them in one dashboard.",
         "AI / Web", "#ff3d9a"),
        ("nvs3d", "nvs3d",
         "NeRF and 3D Gaussian Splatting built from scratch in PyTorch.",
         "Python", "#3776ab"),
        ("Crisis_App", "SankatMitra",
         "Flutter app built to help people during a crisis.",
         "Dart", "#00b4ab"),
    ],
    "footer": "thanks for dropping into my universe",
}
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
ART = os.path.join(ROOT, "tools", "art")

RED, CYN, MAG, ICE, NAVY, GRN = "#ff2a3d", "#2de2ff", "#ff3d9a", "#d8ecff", "#071226", "#3dffa2"
SANS = "'Segoe UI Variable Display','Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'Cascadia Code','SF Mono',Consolas,'Courier New',monospace"

BASE_CSS = """
.gc{animation:gc 6s steps(1) infinite}.gm{animation:gm 6s steps(1) infinite}
@keyframes gc{0%,88%,100%{transform:translate(-2px,0)}90%{transform:translate(-11px,2px)}92%{transform:translate(6px,-1px)}94%{transform:translate(-7px,0)}}
@keyframes gm{0%,88%,100%{transform:translate(2px,0)}90%{transform:translate(10px,-2px)}92%{transform:translate(-6px,1px)}94%{transform:translate(8px,0)}}
.shine{animation:shine 8s ease-in-out infinite}
@keyframes shine{0%{transform:translateX(0)}28%,100%{transform:translateX(1700px)}}
.blob{transform-box:fill-box;transform-origin:center;animation:blob ease-in-out infinite alternate}
@keyframes blob{0%{transform:translate(0,0) scale(1)}50%{transform:translate(90px,-40px) scale(1.25)}100%{transform:translate(-70px,50px) scale(.9)}}
.in{animation:in .9s cubic-bezier(.2,.8,.2,1) both}
@keyframes in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.45;transform:scale(1.6)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""

GLASS_DEFS = """
<filter id="frost" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="16"/><feColorMatrix type="saturate" values="1.3"/></filter>
<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="40"/></filter>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feGaussianBlur stdDeviation="16"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .08 0"/></filter>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset=".35" stop-color="#fff" stop-opacity=".18"/><stop offset=".7" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" stop-opacity=".5"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".26"/><stop offset=".45" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity=".02"/></linearGradient>
<linearGradient id="shineG" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b64(name):
    with open(os.path.join(ART, name), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  assets/{name}  ({len(content)//1024} KB)")


def svg(w, h, label, css, defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{esc(label)}">'
            f'<defs><style>{BASE_CSS}{css}</style>{GLASS_DEFS}{defs}</defs>{body}</svg>')


def glass(cid, x, y, w, h, r, backdrop, tint=NAVY, tint_op=.30, shine_delay=0.0):
    """Frosted glass panel: blurred copy of whatever is behind it + tint + grain + edge light."""
    return (
        f'<rect x="{x}" y="{y+14}" width="{w}" height="{h}" rx="{r}" fill="#01050f" opacity=".45" filter="url(#shadow)"/>'
        f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>'
        f'<g clip-path="url(#{cid})">'
        f'<g filter="url(#frost)">{backdrop}</g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{tint}" opacity="{tint_op}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#sheen)"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" filter="url(#grain)"/>'
        f'<g transform="skewX(-20)"><rect class="shine" style="animation-delay:{shine_delay}s" '
        f'x="{x-260}" y="{y-40}" width="130" height="{h+80}" fill="url(#shineG)"/></g>'
        f'</g>'
        f'<rect x="{x+.75}" y="{y+.75}" width="{w-1.5}" height="{h-1.5}" rx="{r}" fill="none" '
        f'stroke="url(#edge)" stroke-width="1.5"/>')


def glitch_text(x, y, text, size, weight=900, anchor="start", extra=""):
    base = (f'x="{x}" y="{y}" text-anchor="{anchor}" font-family="{SANS}" font-size="{size}" '
            f'font-weight="{weight}" {extra}')
    t = esc(text)
    return (f'<text class="gc" {base} fill="{CYN}" opacity=".9">{t}</text>'
            f'<text class="gm" {base} fill="{RED}" opacity=".9">{t}</text>'
            f'<text {base} fill="#fff">{t}</text>')


def spider(color, s=1.0, op=1.0):
    legs = []
    for side in (-1, 1):
        for i, (a, b) in enumerate([(-30, -60), (-8, -20), (12, 25), (32, 60)]):
            y1 = -3 + i * 2.5
            legs.append(f'M{side*4} {y1:.1f} L{side*(11+i)} {y1 + a*.18:.1f} L{side*(15+i*1.5)} {y1 + b*.22:.1f}')
    return (f'<g transform="scale({s})" opacity="{op}"><path d="{" ".join(legs)}" stroke="{color}" '
            f'stroke-width="1.8" fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<ellipse cx="0" cy="3" rx="5" ry="7.5" fill="{color}"/><circle cx="0" cy="-5.5" r="3.8" fill="{color}"/></g>')


def haze_scene(w, h, seed, ox=0, oy=0, zoom=1.0):
    """Dreamy blurred city colours + drifting light blobs (sits behind the glass)."""
    rnd = random.Random(seed)
    blobs = []
    for col in (RED, CYN, MAG, "#5a8dff", CYN):
        bx, by = rnd.uniform(.05, .95) * w, rnd.uniform(.1, .9) * h
        r = rnd.uniform(.16, .3) * max(w, h) * .6
        blobs.append(f'<circle class="blob" style="animation-duration:{rnd.uniform(9,16):.1f}s;'
                     f'animation-delay:-{rnd.uniform(0,10):.1f}s" cx="{bx:.0f}" cy="{by:.0f}" r="{r:.0f}" '
                     f'fill="{col}" opacity="{rnd.uniform(.35,.6):.2f}"/>')
    return (f'<image href="{HAZE}" x="{ox - w*(zoom-1)/2:.0f}" y="{oy - h*(zoom-1)/2:.0f}" '
            f'width="{w*zoom:.0f}" height="{h*zoom:.0f}" preserveAspectRatio="xMidYMid slice"/>'
            f'<rect width="{w}" height="{h}" fill="{NAVY}" opacity=".35"/>'
            f'<g filter="url(#soft)">{"".join(blobs)}</g>')


def framed(w, h, r, inner):
    return (f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="{r}"/></clipPath>'
            f'<g clip-path="url(#frame)">{inner}</g>'
            f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="{r}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>')


def wrap(text, n):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > n and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + ([cur] if cur else [])


# ------------------------------------------------------------------- HERO --
def build_hero():
    W, H = 1200, 675
    rnd = random.Random(1610)
    roles = CONFIG["roles"]
    n = len(roles)
    cx, cy, cw, ch = 742, 140, 418, 392

    css = f"""
.kb{{transform-origin:600px 337px;animation:kb 22s ease-in-out infinite alternate}}
@keyframes kb{{from{{transform:scale(1.02) translate(0,0)}}to{{transform:scale(1.1) translate(-14px,10px)}}}}
.gr,.gb{{opacity:0;animation:gl 7s steps(1) infinite}}
.gb{{animation-delay:.12s}}
@keyframes gl{{0%,86%,100%{{opacity:0;transform:none}}87%{{opacity:.7;transform:translate(14px,0)}}89%{{opacity:.6;transform:translate(-10px,0)}}91%{{opacity:.7;transform:translate(6px,0)}}93%{{opacity:0}}}}
.rise{{animation:rise linear infinite}}
@keyframes rise{{from{{transform:translateY(0)}}to{{transform:translateY(-760px)}}}}
.shard{{transform-box:fill-box;transform-origin:center;animation:shard ease-in-out infinite alternate}}
@keyframes shard{{from{{transform:translate(0,0) rotate(0)}}to{{transform:translate(10px,-26px) rotate(14deg)}}}}
.role{{opacity:0;animation:role {n*3}s infinite}}
@keyframes role{{0%{{opacity:0;transform:translateY(10px)}}{100/n*.1:.1f}%,{100/n*.85:.1f}%{{opacity:1;transform:none}}{100/n:.1f}%,100%{{opacity:0;transform:translateY(-10px)}}}}
.cur{{animation:cur 1s steps(1) infinite}}@keyframes cur{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.role.r0{{opacity:1}}}}
"""
    defs = (f'<image id="poster" href="{POSTER}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>'
            f'<filter id="ronly"><feColorMatrix values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter>'
            f'<filter id="conly"><feColorMatrix values="0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0"/></filter>'
            f'<clipPath id="bands"><rect y="70" width="{W}" height="26"/><rect y="210" width="{W}" height="12"/>'
            f'<rect y="330" width="{W}" height="40"/><rect y="520" width="{W}" height="18"/></clipPath>'
            f'<radialGradient id="vig" cx=".42" cy=".42" r=".8"><stop offset=".55" stop-color="#030a18" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#030a18" stop-opacity=".75"/></radialGradient>'
            f'<linearGradient id="shardG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity=".04"/></linearGradient>'
            f'<pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.6" fill="{RED}"/></pattern>'
            f'<radialGradient id="dm" cx="0" cy="1" r=".55"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="dmask"><rect width="{W}" height="{H}" fill="url(#dm)"/></mask>'
            f'<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{CYN}"/><stop offset=".5" stop-color="{MAG}"/>'
            f'<stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>')

    poster = '<g class="kb"><use href="#poster"/></g>'
    glitch = (f'<g class="kb"><g clip-path="url(#bands)">'
              f'<g class="gr" style="mix-blend-mode:screen"><use href="#poster" filter="url(#ronly)"/></g>'
              f'<g class="gb" style="mix-blend-mode:screen"><use href="#poster" filter="url(#conly)"/></g></g></g>')

    shards = []
    for (x, y, s, d) in [(70, 80, 1.0, 7), (250, 560, .8, 9), (580, 610, .6, 6),
                         (640, 70, .7, 8), (1120, 70, .9, 10), (1010, 600, .7, 7.5),
                         (60, 360, .55, 6.5), (690, 330, .45, 8.5)]:
        pts = [(0, 0), (60, -12), (78, 40), (22, 66)] if rnd.random() < .5 else [(0, 0), (70, 10), (30, 62)]
        p = " ".join(f"{x + px*s:.0f},{y + py*s:.0f}" for px, py in pts)
        shards.append(f'<polygon class="shard" style="animation-duration:{d}s;animation-delay:-{rnd.uniform(0,6):.1f}s" '
                      f'points="{p}" fill="url(#shardG)" stroke="#fff" stroke-opacity=".6" stroke-width="1"/>')

    motes = []
    for _ in range(55):
        x = rnd.uniform(0, W)
        y = rnd.uniform(H, H + 60)
        col = rnd.choice(["#fff", "#fff", CYN, MAG])
        if rnd.random() < .35:
            ln = rnd.uniform(14, 40)
            shape = (f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y+ln:.0f}" stroke="{col}" '
                     f'stroke-width="1.3" stroke-linecap="round"/>')
        else:
            shape = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1,2.6):.1f}" fill="{col}"/>'
        motes.append(f'<g class="rise" opacity="{rnd.uniform(.25,.8):.2f}" style="animation-duration:'
                     f'{rnd.uniform(5,12):.1f}s;animation-delay:-{rnd.uniform(0,12):.1f}s">{shape}</g>')

    name = CONFIG["name"].upper()
    nsize = int(min(92, 360 / (0.64 * max(len(name), 1))))
    tx = cx + 34
    roles_svg = "".join(
        f'<text class="role r{i}" style="animation-delay:{i*3}s" x="{tx}" y="{cy+282}" font-family="{MONO}" '
        f'font-size="17" font-weight="700" fill="{CYN}">&gt; {esc(r)}<tspan class="cur">_</tspan></text>'
        for i, r in enumerate(roles))
    pill_w = len(CONFIG["status"]) * 8.6 + 52
    card_content = (
        f'<text x="{tx}" y="{cy+46}" font-family="{MONO}" font-size="12.5" fill="{ICE}" letter-spacing="3.5" opacity=".85">EARTH-1610 // DEV-VERSE</text>'
        f'<g transform="translate({cx+cw-42} {cy+40})">{spider(RED, 1.15)}</g>'
        f'<text x="{tx}" y="{cy+100}" font-family="{SANS}" font-size="19" font-weight="600" fill="#fff" letter-spacing="6" opacity=".9">{esc(CONFIG["greeting"])}</text>'
        + glitch_text(tx - 3, cy + 100 + nsize * .95, name, nsize, 900, extra='letter-spacing="1"')
        + f'<text x="{tx}" y="{cy+226}" font-family="{SANS}" font-size="19" font-style="italic" fill="#fff" opacity=".92">{esc(CONFIG["tagline"])}</text>'
        f'<rect x="{tx}" y="{cy+246}" width="{cw-68}" height="2" fill="url(#rule)"/>'
        + roles_svg
        + f'<g transform="translate({tx} {cy+314})"><rect width="{pill_w:.0f}" height="36" rx="18" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".4"/>'
        f'<circle class="pulse" cx="20" cy="18" r="5" fill="{GRN}"/><circle cx="20" cy="18" r="5" fill="{GRN}"/>'
        f'<text x="36" y="23.5" font-family="{SANS}" font-size="15" font-weight="600" fill="#fff">{esc(CONFIG["status"])}</text></g>')

    inner = (
        poster + glitch
        + f'<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dmask)" opacity=".35"/>'
        + f'<rect width="{W}" height="{H}" fill="url(#vig)"/>'
        + "".join(motes) + "".join(shards)
        + glass("card", cx, cy, cw, ch, 26, poster, tint_op=.45, shine_delay=1.5)
        + card_content)
    write("hero.svg", svg(W, H, f'{CONFIG["name"]} — Spider-Verse banner', css, defs, framed(W, H, 26, inner)))


# ---------------------------------------------------------------- ID CARD --
def build_id():
    W, H = 1200, 500
    css = """
.scan{animation:scan 4s ease-in-out infinite}
@keyframes scan{0%{transform:translateY(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateY(370px);opacity:0}}
.holo{animation:holo 6s linear infinite}@keyframes holo{to{transform:translateX(-600px)}}
"""
    defs = (f'<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYN}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{CYN}" stop-opacity=".55"/></linearGradient>'
            f'<linearGradient id="holoG" x1="0" x2="1" spreadMethod="repeat"><stop offset="0" stop-color="{CYN}"/>'
            f'<stop offset=".25" stop-color="{MAG}"/><stop offset=".5" stop-color="#ffe14d"/><stop offset=".75" stop-color="{RED}"/>'
            f'<stop offset="1" stop-color="{CYN}"/></linearGradient>'
            f'<clipPath id="pc"><rect x="52" y="72" width="330" height="385" rx="18"/></clipPath>'
            f'<clipPath id="hc"><rect x="430" y="428" width="480" height="8" rx="4"/></clipPath>')
    scene = haze_scene(W, H, 7)
    rnd = random.Random(5)
    bars, bx = [], 960
    while bx < 1148:
        bw = rnd.choice([1.5, 2, 3, 4.5])
        bars.append(f'<rect x="{bx:.1f}" y="410" width="{bw}" height="38" fill="#fff" opacity=".8"/>')
        bx += bw + rnd.choice([1.5, 2.5, 3.5])

    rows = []
    for i, (k, v) in enumerate(CONFIG["id_rows"]):
        y = 118 + i * 50
        rows.append(f'<g class="in" style="animation-delay:{.2 + i*.15:.2f}s">'
                    f'<text x="430" y="{y}" font-family="{MONO}" font-size="12" fill="{CYN}" letter-spacing="4">{esc(k)}</text>'
                    f'<text x="430" y="{y+26}" font-family="{SANS}" font-size="22" font-weight="600" fill="#fff">{esc(v)}</text></g>')

    corners = "".join(
        f'<path d="M{x} {y+18*sy} L{x} {y} L{x+18*sx} {y}" stroke="#fff" stroke-width="2.5" fill="none" opacity=".9"/>'
        for x, y, sx, sy in [(64, 84, 1, 1), (370, 84, -1, 1), (64, 445, 1, -1), (370, 445, -1, -1)])
    inner = (
        scene
        + glass("g", 20, 20, W - 40, H - 40, 26, scene, shine_delay=3)
        + f'<text x="52" y="54" font-family="{MONO}" font-size="14" font-weight="700" fill="#fff" letter-spacing="7">SPIDER-ID</text>'
        f'<text x="{W-52}" y="54" text-anchor="end" font-family="{MONO}" font-size="12" fill="{ICE}" letter-spacing="3" opacity=".75">'
        f'ISSUED BY THE MULTIVERSE  ·  No. {esc(CONFIG["login"])}</text>'
        f'<g transform="translate(1050 250)">{spider("#fff", 7, .07)}</g>'
        f'<g clip-path="url(#pc)"><image href="{PORTRAIT}" x="52" y="72" width="330" height="385" preserveAspectRatio="xMidYMid slice"/>'
        f'<rect class="scan" x="52" y="40" width="330" height="40" fill="url(#scanG)"/></g>'
        f'<rect x="52.75" y="72.75" width="328.5" height="383.5" rx="18" fill="none" stroke="url(#edge)" stroke-width="1.5"/>'
        + corners + "".join(rows)
        + f'<g clip-path="url(#hc)"><rect class="holo" x="430" y="428" width="1200" height="8" fill="url(#holoG)"/></g>'
        + "".join(bars))
    write("id-card.svg", svg(W, H, "Spider-ID", css, defs, framed(W, H, 26, inner)))


# ------------------------------------------------------------------ STACK --
def build_stack():
    W = 1200
    chips, x, y = [], 48, 100
    for i, (name, col) in enumerate(CONFIG["stack"]):
        cw = len(name) * 10.2 + 58
        if x + cw > W - 48:
            x, y = 48, y + 64
        chips.append(
            f'<g class="in" style="animation-delay:{.1 + i*.07:.2f}s"><g class="bob" style="animation-delay:-{i*.4:.1f}s">'
            f'<rect x="{x}" y="{y}" width="{cw:.0f}" height="46" rx="23" fill="#fff" fill-opacity=".1" stroke="#fff" stroke-opacity=".38"/>'
            f'<rect x="{x}" y="{y}" width="{cw:.0f}" height="23" rx="11.5" fill="#fff" fill-opacity=".07"/>'
            f'<circle cx="{x+24}" cy="{y+23}" r="9" fill="{col}" opacity=".35"/><circle cx="{x+24}" cy="{y+23}" r="5.5" fill="{col}"/>'
            f'<text x="{x+40}" y="{y+29.5}" font-family="{SANS}" font-size="17" font-weight="600" fill="#fff">{esc(name)}</text></g></g>')
        x += cw + 14
    H = y + 46 + 44
    css = ".bob{animation:bob 4s ease-in-out infinite}@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}"
    scene = haze_scene(W, H, 21, zoom=1.4)
    inner = (scene + glass("g", 20, 20, W - 40, H - 40, 24, scene, shine_delay=5)
             + f'<text x="48" y="66" font-family="{MONO}" font-size="14" font-weight="700" fill="#fff" letter-spacing="7">WEB-SHOOTER LOADOUT</text>'
             f'<text x="{W-48}" y="66" text-anchor="end" font-family="{MONO}" font-size="12" fill="{ICE}" letter-spacing="3" opacity=".75">TOOLS I SWING WITH</text>'
             + "".join(chips))
    write("stack.svg", svg(W, H, "Tech stack", css, "", framed(W, H, 24, inner)))


# --------------------------------------------------------------- PROJECTS --
def build_projects():
    W, H = 600, 300
    for i, (repo, title, desc, lang, col) in enumerate(CONFIG["projects"], 1):
        scene = haze_scene(W, H, 100 + i * 13, ox=(i % 2) * -120, zoom=1.8)
        lines = wrap(desc, 46)[:3]
        body = "".join(f'<text x="44" y="{150 + j*25}" font-family="{SANS}" font-size="17" fill="#fff" opacity=".86">{esc(l)}</text>'
                       for j, l in enumerate(lines))
        inner = (scene + glass("g", 14, 14, W - 28, H - 28, 22, scene, shine_delay=i * 1.7)
                 + f'<text x="{W-40}" y="112" text-anchor="end" font-family="{SANS}" font-size="104" font-weight="900" '
                 f'fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="1.5">0{i}</text>'
                 f'<text x="44" y="62" font-family="{MONO}" font-size="12" fill="{CYN}" letter-spacing="4">DIMENSION 0{i}</text>'
                 + glitch_text(42, 110, title, 34, 800)
                 + body
                 + f'<circle cx="52" cy="250" r="6" fill="{col}"/><text x="66" y="255.5" font-family="{SANS}" font-size="15" '
                 f'font-weight="600" fill="#fff" opacity=".9">{esc(lang)}</text>'
                 f'<g transform="translate({W-178} 230)"><rect width="134" height="38" rx="19" fill="#fff" fill-opacity=".12" stroke="#fff" stroke-opacity=".45"/>'
                 f'<text x="67" y="24.5" text-anchor="middle" font-family="{MONO}" font-size="12.5" font-weight="700" fill="#fff" letter-spacing="2">OPEN REPO →</text></g>')
        write(f"project-{i}.svg", svg(W, H, title, "", "", framed(W, H, 22, inner)))


# ------------------------------------------------------------------ STATS --
QUERY = """query($l:String!){user(login:$l){followers{totalCount}
contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionLevel}}}}
repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount
nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("  (no GITHUB_TOKEN: skipping live stats)")
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"l": CONFIG["login"]}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-builder"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]
    except Exception as e:  # keep the old card if the API hiccups
        print(f"  stats fetch failed: {e}")
        return None
    langs = {}
    for repo in data["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#888"])[0] += e["size"]
    cal = data["contributionsCollection"]["contributionCalendar"]
    return {
        "repos": data["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in data["repositories"]["nodes"]),
        "followers": data["followers"]["totalCount"],
        "contribs": cal["totalContributions"],
        "weeks": [[d["contributionLevel"] for d in w["contributionDays"]] for w in cal["weeks"]],
        "langs": sorted(langs.items(), key=lambda kv: -kv[1][0])[:5],
    }


def build_stats():
    s = fetch_stats()
    if not s:
        return
    W, H = 1200, 470
    css = """
.sweep{opacity:0;animation:sweep 5s ease-in-out infinite}
@keyframes sweep{0%{transform:translateX(0);opacity:0}10%{opacity:1}70%{opacity:1}80%,100%{transform:translateX(860px);opacity:0}}
"""
    defs = (f'<linearGradient id="swG" x1="0" x2="1"><stop offset="0" stop-color="{CYN}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{CYN}" stop-opacity=".5"/></linearGradient>')
    scene = haze_scene(W, H, 77, zoom=1.3)
    tiles = []
    for i, (val, lab) in enumerate([(s["contribs"], "CONTRIBUTIONS / YR"), (s["repos"], "PUBLIC REPOS"),
                                    (s["stars"], "STARS EARNED"), (s["followers"], "FOLLOWERS")]):
        x = 48 + i * 280
        tiles.append(f'<g class="in" style="animation-delay:{.1+i*.12:.2f}s">'
                     f'<rect x="{x}" y="88" width="258" height="112" rx="18" fill="#fff" fill-opacity=".09" stroke="#fff" stroke-opacity=".32"/>'
                     f'<text x="{x+24}" y="150" font-family="{SANS}" font-size="46" font-weight="800" fill="#fff">{val:,}</text>'
                     f'<text x="{x+24}" y="180" font-family="{MONO}" font-size="11.5" fill="{CYN}" letter-spacing="3">{lab}</text></g>')
    lvl = {"NONE": ("#fff", .08), "FIRST_QUARTILE": (CYN, .4), "SECOND_QUARTILE": (CYN, .8),
           "THIRD_QUARTILE": (MAG, .85), "FOURTH_QUARTILE": (RED, 1)}
    cells = []
    for wi, week in enumerate(s["weeks"][-53:]):
        for di, l in enumerate(week):
            c, o = lvl.get(l, lvl["NONE"])
            cells.append(f'<rect x="{48 + wi*15.6:.1f}" y="{262 + di*15.6:.1f}" width="12" height="12" rx="3" fill="{c}" opacity="{o}"/>')
    total = sum(v[0] for _, v in s["langs"]) or 1
    bar, legend, bx = [], [], 0
    for i, (name, (size, col)) in enumerate(s["langs"]):
        w = 230 * size / total
        bar.append(f'<rect x="{922+bx:.1f}" y="268" width="{max(w,2):.1f}" height="12" fill="{col}"/>')
        legend.append(f'<circle cx="930" cy="{312+i*28}" r="6" fill="{col}"/>'
                      f'<text x="946" y="{317+i*28}" font-family="{SANS}" font-size="15" fill="#fff">{esc(name)}</text>'
                      f'<text x="1152" y="{317+i*28}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{ICE}" opacity=".8">{100*size/total:.1f}%</text>')
        bx += w
    today = datetime.date.today().isoformat()
    inner = (scene + glass("g", 20, 20, W - 40, H - 40, 26, scene, shine_delay=2)
             + f'<text x="48" y="64" font-family="{MONO}" font-size="14" font-weight="700" fill="#fff" letter-spacing="7">SPIDER-SENSE</text>'
             f'<text x="{W-48}" y="64" text-anchor="end" font-family="{MONO}" font-size="12" fill="{ICE}" letter-spacing="3" opacity=".75">LIVE · SYNCED {today}</text>'
             + "".join(tiles)
             + f'<text x="48" y="246" font-family="{MONO}" font-size="11.5" fill="{CYN}" letter-spacing="3">WEB ACTIVITY · LAST 12 MONTHS</text>'
             + "".join(cells)
             + f'<rect class="sweep" x="20" y="258" width="60" height="112" fill="url(#swG)"/>'
             f'<text x="922" y="246" font-family="{MONO}" font-size="11.5" fill="{CYN}" letter-spacing="3">TOP LANGUAGES</text>'
             f'<clipPath id="bc"><rect x="922" y="268" width="230" height="12" rx="6"/></clipPath><g clip-path="url(#bc)">{"".join(bar)}</g>'
             + "".join(legend))
    write("stats.svg", svg(W, H, "GitHub stats", css, defs, framed(W, H, 26, inner)))


# ----------------------------------------------------------------- FOOTER --
def swinger(color, accent):
    limb = f'fill="none" stroke="{color}" stroke-linecap="round" stroke-linejoin="round"'
    return (f'<path d="M0 0 L-4 22 L-6 42" {limb} stroke-width="9"/><path d="M-4 46 L-30 60 L-44 52" {limb} stroke-width="9"/>'
            f'<path d="M-8 40 Q4 38 8 52 L6 92 Q-8 98 -16 90 Z" fill="{color}"/><ellipse cx="12" cy="34" rx="11" ry="12" fill="{color}"/>'
            f'<path d="M-4 88 L18 108 L4 134" {limb} stroke-width="11"/><path d="M-10 90 L-22 118 L-40 128" {limb} stroke-width="11"/>'
            f'<path d="M8 32 L19 28 L17 37 Z" fill="#fff"/><circle r="4.5" fill="{accent}"/>'
            f'<g transform="translate(-2 66) scale(.5)">{spider(accent)}</g>')


def build_footer():
    W, H = 1200, 220
    css = f"""
.cross{{animation:cross 8s linear infinite}}@keyframes cross{{from{{transform:translateX(-150px)}}to{{transform:translateX({W+150}px)}}}}
.pend{{animation:pend 1.33s ease-in-out infinite alternate}}@keyframes pend{{from{{transform:rotate(40deg)}}to{{transform:rotate(-40deg)}}}}
@media (prefers-reduced-motion:reduce){{.cross{{transform:translateX(190px)!important}}}}
"""
    scene = haze_scene(W, H, 55, zoom=1.5)
    hero = (f'<g class="cross"><g transform="translate(0 -10)"><g class="pend">'
            f'<line x1="0" y1="0" x2="0" y2="104" stroke="#fff" stroke-width="1.6" opacity=".9"/>'
            f'<g transform="translate(0 104) scale(.58)">{swinger("#0b1630", RED)}</g></g></g></g>')
    inner = (scene + hero + glass("g", 330, 46, 540, 128, 64, scene + hero, shine_delay=1)
             + glitch_text(600, 112, "KEEP SWINGING", 40, 900, "middle", 'letter-spacing="3"')
             + f'<text x="600" y="144" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{ICE}" letter-spacing="2">{esc(CONFIG["footer"])}</text>')
    write("footer.svg", svg(W, H, "keep swinging", css, "", framed(W, H, 24, inner)))


HAZE = POSTER = PORTRAIT = ""

if __name__ == "__main__":
    HAZE = b64("haze.jpg")
    print("building assets...")
    if "--stats" not in sys.argv:
        POSTER, PORTRAIT = b64("hero.jpg"), b64("portrait.jpg")
        build_hero()
        build_id()
        build_stack()
        build_projects()
        build_footer()
    build_stats()
    print("done.")
