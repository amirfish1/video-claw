#!/usr/bin/env python3
"""v2.7.1 asset updates (from the converged v2.7 critique).

Regenerates only the 3 CHANGED overlays into review-room/v2.7.1/assets/:
  - diagram_corporate.png  : raised so AGENT BENCH clears the caption box
  - group_chat_overlay.png : header "TEAM · group chat" -> "AGENT · group chat"
  - founder_labeled.png    : coworker side-regions dimmed+desaturated, founder full
                             color, gold label higher contrast + nudged off top edge
Unchanged assets (empty_debate_room, deck_agent, music, subbass) are referenced from
../v2.7/assets by the v2.7.1 assembler.
Run: python3 review-room/v2.7.1/build_assets_v271.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "review-room" / "v2.7" / "assets"          # source frame
OUT = ROOT / "review-room" / "v2.7.1" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080

BG = (12, 15, 20)
AMBER = (217, 119, 6)
AMBER_HOT = (255, 176, 32)
INDIGO = (59, 130, 246)
TEAL = (13, 148, 136)
INK = (232, 236, 242)
MUTE = (150, 160, 172)
FONTS = "/System/Library/Fonts/Supplemental/"
SYS = "/System/Library/Fonts/"


def font(name, size, bold=False):
    cands = [SYS + "Menlo.ttc"] if name == "mono" else [FONTS + ("Arial Bold.ttf" if bold else "Arial.ttf")]
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            pass
    return ImageFont.load_default()


def ctext(d, cx, y, t, f, fill):
    d.text((cx - d.textlength(t, font=f) / 2, y), t, font=f, fill=fill)


# -------- diagram (raised: nothing below ~y838) --------
def diagram():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    cx = W // 2
    f_node = font("arial", 40, bold=True); f_sub = font("arial", 30); f_small = font("arial", 26)
    n1 = (cx - 280, 70, cx + 280, 190)
    n2 = (cx - 280, 350, cx + 280, 470)
    n3 = (cx - 440, 620, cx + 440, 838)
    d.line([(cx, n1[3]), (cx, n2[1])], fill=(90, 100, 115), width=4)
    d.line([(cx, n2[3]), (cx, n3[1])], fill=(90, 100, 115), width=4)
    rx = n3[2] + 70
    d.line([(n3[2], (n3[1]+n3[3])//2), (rx, (n3[1]+n3[3])//2)], fill=(70, 90, 110), width=3)
    d.line([(rx, (n3[1]+n3[3])//2), (rx, (n2[1]+n2[3])//2)], fill=(70, 90, 110), width=3)
    d.line([(rx, (n2[1]+n2[3])//2), (n2[2], (n2[1]+n2[3])//2)], fill=(70, 90, 110), width=3)
    d.text((rx + 12, (n2[3]+n3[1])//2 - 16), "refine", font=f_small, fill=MUTE)
    for (px, py) in [(cx, (n1[3]+n2[1])//2), (cx, (n2[3]+n3[1])//2)]:
        d.ellipse([px-8, py-8, px+8, py+8], fill=AMBER)
    d.rounded_rectangle(n1, 22, fill=(22, 27, 34), outline=AMBER, width=4)
    ctext(d, cx, n1[1]+22, "FOUNDER INPUT", f_node, AMBER); ctext(d, cx, n1[1]+74, "the brief · the notes", f_small, MUTE)
    d.rounded_rectangle(n2, 22, fill=(22, 27, 34), outline=INDIGO, width=4)
    ctext(d, cx, n2[1]+22, "COORDINATOR AGENT", f_node, INDIGO); ctext(d, cx, n2[1]+74, "keeps every role in sync", f_small, MUTE)
    d.rounded_rectangle(n3, 22, fill=(22, 27, 34), outline=TEAL, width=4)
    ctext(d, cx, n3[1]+22, "AGENT BENCH", f_node, TEAL)
    subs = ["Copywriter", "Audience Planner", "Designer"]; sw = (n3[2]-n3[0])/3
    for i, s in enumerate(subs):
        scx = int(n3[0] + sw*(i+0.5)); chip = (scx-138, n3[1]+104, scx+138, n3[1]+168)
        d.rounded_rectangle(chip, 16, fill=(16, 40, 38), outline=(20, 90, 84), width=2)
        ctext(d, scx, n3[1]+118, s, f_sub, (190, 230, 224))
    img.save(OUT / "diagram_corporate.png"); print("diagram_corporate.png (raised)")


# -------- group chat (AGENT rename) --------
def chat():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    panel = (1180, 150, 1860, 930)
    d.rounded_rectangle(panel, 26, fill=(14, 17, 23, 235), outline=(60, 70, 85, 255), width=2)
    f_hdr = font("arial", 30, bold=True); f_name = font("arial", 26, bold=True); f_msg = font("arial", 27)
    d.text((panel[0]+34, panel[1]+28), "AGENT  ·  group chat", font=f_hdr, fill=(180, 190, 205, 255))
    d.line([(panel[0]+30, panel[1]+78), (panel[2]-30, panel[1]+78)], fill=(60, 70, 85, 255), width=2)
    msgs = [
        (TEAL, "Copywriter Agent", ["Lead with the promise —", "save five hours a week."]),
        (INDIGO, "Brand Agent", ["No — open on the pain.", "You're drowning in posts."]),
        (AMBER, "Coordinator", ["Headline locked.", "Handed to Deck Agent."]),
    ]
    y = panel[1]+104; x = panel[0]+34
    for color, name, lines in msgs:
        d.ellipse([x, y+4, x+18, y+22], fill=color + (255,))
        d.text((x+30, y), name, font=f_name, fill=color + (255,)); y += 38
        for ln in lines:
            d.text((x+30, y), ln, font=f_msg, fill=INK + (255,)); y += 36
        y += 22
    img.save(OUT / "group_chat_overlay.png"); print("group_chat_overlay.png (AGENT)")


# -------- founder labeled (isolation: dim/desat sides, founder full color) --------
def founder():
    base = Image.open(SRC / "founder_frame.png").convert("RGB")
    dim = ImageEnhance.Color(base).enhance(0.22)
    dim = ImageEnhance.Brightness(dim).enhance(0.5)
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    md.rectangle([655, 0, 1305, H], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(70))
    iso = Image.composite(base, dim, mask).convert("RGBA")
    d = ImageDraw.Draw(iso)
    f_lbl = font("arial", 28, bold=True)

    def box(b, color, text, emph=False):
        d.rounded_rectangle(b, 14, outline=color, width=8 if emph else 4)
        tw = d.textlength(text, font=f_lbl); lx, ly = b[0], b[1]-44
        d.rounded_rectangle((lx, ly, lx+tw+28, ly+38), 8, fill=(10, 12, 16, 240), outline=color, width=2)
        d.text((lx+14, ly+5), text, font=f_lbl, fill=color)
    box((60, 175, 600, 980), TEAL + (255,), "[ AGENT · Audience Planner ]")
    box((1360, 180, 1880, 990), TEAL + (255,), "[ AGENT · Copywriter ]")
    box((690, 130, 1290, 1000), AMBER_HOT + (255,), "[ HUMAN · Founder ]", emph=True)
    iso.convert("RGB").save(OUT / "founder_labeled.png"); print("founder_labeled.png (isolated)")


if __name__ == "__main__":
    diagram(); chat(); founder()
    print("v2.7.1 assets ->", OUT)
