#!/usr/bin/env python3
"""Build v2.7 text/overlay assets as crisp PIL PNGs (no ffmpeg drawtext garble).

Outputs (1920x1080) into review-room/v2.7/assets/:
  - diagram_corporate.png     (opaque) 3-node corporate-flow orchestration
  - group_chat_overlay.png    (RGBA)   right-margin agent chat panel
  - deck_agent_overlay.png    (RGBA)   Deck-Agent status card (Codex copy verbatim)
  - founder_labels_overlay.png(RGBA)   t45 AGENT/HUMAN label boxes

empty_debate_room.png is produced separately (nanobanana inpaint of sample5).
Run: python3 review-room/v2.7/build_assets.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "review-room" / "v2.7" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080

# palette (locked in the writers'-room)
BG = (12, 15, 20, 255)          # #0c0f14
AMBER = (217, 119, 6, 255)      # #D97706 founder/human
INDIGO = (59, 130, 246, 255)    # #3B82F6 coordinator
TEAL = (13, 148, 136, 255)      # #0D9488 agents
INK = (232, 236, 242, 255)
MUTE = (150, 160, 172, 255)

FONTS = "/System/Library/Fonts/Supplemental/"
SYS = "/System/Library/Fonts/"


def font(name, size, bold=False):
    cands = []
    if name == "mono":
        cands = [SYS + "Menlo.ttc", FONTS + "Courier New.ttf"]
    else:
        cands = [FONTS + ("Arial Bold.ttf" if bold else "Arial.ttf")]
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def rrect(d, box, radius, fill=None, outline=None, width=3):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(d, cx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return w


# ---------------------------------------------------------------- diagram
def build_diagram():
    img = Image.new("RGB", (W, H), BG[:3])
    d = ImageDraw.Draw(img)
    cx = W // 2
    f_node = font("arial", 40, bold=True)
    f_sub = font("arial", 30)
    f_small = font("arial", 26)

    # node geometry (vertical hierarchy)
    n1 = (cx - 280, 110, cx + 280, 235)     # FOUNDER INPUT
    n2 = (cx - 280, 450, cx + 280, 575)     # COORDINATOR AGENT
    n3 = (cx - 440, 790, cx + 440, 1000)    # AGENT BENCH (taller, sub-labels)

    # connectors first (under nodes)
    d.line([(cx, n1[3]), (cx, n2[1])], fill=(90, 100, 115), width=4)
    d.line([(cx, n2[3]), (cx, n3[1])], fill=(90, 100, 115), width=4)
    # return loop (right side, bench -> coordinator)
    rx = n3[2] + 70
    d.line([(n3[2], (n3[1] + n3[3]) // 2), (rx, (n3[1] + n3[3]) // 2)], fill=(70, 90, 110), width=3)
    d.line([(rx, (n3[1] + n3[3]) // 2), (rx, (n2[1] + n2[3]) // 2)], fill=(70, 90, 110), width=3)
    d.line([(rx, (n2[1] + n2[3]) // 2), (n2[2], (n2[1] + n2[3]) // 2)], fill=(70, 90, 110), width=3)
    d.text((rx + 12, (n2[3] + n3[1]) // 2 - 16), "refine", font=f_small, fill=MUTE)

    # pulse dots on the main spine
    for (px, py) in [(cx, (n1[3] + n2[1]) // 2), (cx, (n2[3] + n3[1]) // 2)]:
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=AMBER[:3])

    # node 1 — FOUNDER INPUT (amber)
    rrect(d, n1, 22, fill=(22, 27, 34), outline=AMBER[:3], width=4)
    center_text(d, cx, n1[1] + 24, "FOUNDER INPUT", f_node, AMBER[:3])
    center_text(d, cx, n1[1] + 76, "the brief · the notes", f_small, MUTE)

    # node 2 — COORDINATOR AGENT (indigo)
    rrect(d, n2, 22, fill=(22, 27, 34), outline=INDIGO[:3], width=4)
    center_text(d, cx, n2[1] + 24, "COORDINATOR AGENT", f_node, INDIGO[:3])
    center_text(d, cx, n2[1] + 76, "keeps every role in sync", f_small, MUTE)

    # node 3 — AGENT BENCH (teal) with 3 sub-labels
    rrect(d, n3, 22, fill=(22, 27, 34), outline=TEAL[:3], width=4)
    center_text(d, cx, n3[1] + 22, "AGENT BENCH", f_node, TEAL[:3])
    subs = ["Copywriter", "Audience Planner", "Designer"]
    sw = (n3[2] - n3[0]) / 3
    for i, s in enumerate(subs):
        scx = int(n3[0] + sw * (i + 0.5))
        chip = (scx - 138, n3[1] + 104, scx + 138, n3[1] + 168)
        rrect(d, chip, 16, fill=(16, 40, 38), outline=(20, 90, 84), width=2)
        center_text(d, scx, n3[1] + 118, s, f_sub, (190, 230, 224))

    img.save(ASSETS / "diagram_corporate.png")
    print("wrote diagram_corporate.png")


# ------------------------------------------------------------- group chat
def build_chat():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    panel = (1180, 150, 1860, 930)
    d.rounded_rectangle(panel, radius=26, fill=(14, 17, 23, 235), outline=(60, 70, 85, 255), width=2)
    f_hdr = font("arial", 30, bold=True)
    f_name = font("arial", 26, bold=True)
    f_msg = font("arial", 27)
    d.text((panel[0] + 34, panel[1] + 28), "TEAM  ·  group chat", font=f_hdr, fill=(180, 190, 205, 255))
    d.line([(panel[0] + 30, panel[1] + 78), (panel[2] - 30, panel[1] + 78)], fill=(60, 70, 85, 255), width=2)

    msgs = [
        (TEAL, "Copywriter Agent", ["Lead with the promise —", "save five hours a week."]),
        (INDIGO, "Brand Agent", ["No — open on the pain.", "You're drowning in posts."]),
        (AMBER, "Coordinator", ["Headline locked.", "Handed to Deck Agent."]),
    ]
    y = panel[1] + 104
    x = panel[0] + 34
    for color, name, lines in msgs:
        d.ellipse([x, y + 4, x + 18, y + 22], fill=color)
        d.text((x + 30, y), name, font=f_name, fill=color)
        y += 38
        for ln in lines:
            d.text((x + 30, y), ln, font=f_msg, fill=INK)
            y += 36
        y += 22
    img.save(ASSETS / "group_chat_overlay.png")
    print("wrote group_chat_overlay.png")


# ------------------------------------------------------------- deck agent
def build_deck():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    card = (140, 250, 980, 720)
    d.rounded_rectangle(card, radius=24, fill=(14, 17, 23, 238), outline=(70, 80, 95, 255), width=2)
    f_hdr = font("arial", 40, bold=True)
    f_title = font("arial", 32, bold=True)
    f_log = font("mono", 28)
    f_status = font("arial", 30, bold=True)
    x = card[0] + 40
    # header chip
    d.rounded_rectangle((x, card[1] + 34, x + 278, card[1] + 90), radius=12, fill=(30, 24, 10, 255), outline=AMBER, width=2)
    d.text((x + 18, card[1] + 42), "DECK AGENT", font=f_hdr, fill=AMBER[:3])
    y = card[1] + 120
    d.text((x, y), "KNEADED.AI  Campaign Concepts v4", font=f_title, fill=INK); y += 64
    for ln in ["Reading founder notes…", "Rebuilding headline options…"]:
        d.text((x, y), ln, font=f_log, fill=MUTE); y += 46
    y += 14
    d.text((x, y), "Ready for founder review", font=f_status, fill=(120, 210, 150)); y += 52
    d.text((x, y), "Presenter:  AI", font=f_status, fill=INDIGO[:3])
    img.save(ASSETS / "deck_agent_overlay.png")
    print("wrote deck_agent_overlay.png")


# --------------------------------------------------------- founder labels
def build_founder_labels():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_lbl = font("arial", 28, bold=True)

    def labeled_box(box, color, text, emphasize=False):
        wdt = 7 if emphasize else 4
        d.rounded_rectangle(box, radius=14, outline=color, width=wdt)
        tw = d.textlength(text, font=f_lbl)
        lx, ly = box[0], box[1] - 44
        d.rounded_rectangle((lx, ly, lx + tw + 28, ly + 38), radius=8, fill=(10, 12, 16, 235), outline=color, width=2)
        d.text((lx + 14, ly + 5), text, font=f_lbl, fill=color)

    # positions measured from founder reprise frame (full 1920x1080, no push-in)
    labeled_box((60, 175, 600, 980), TEAL[:3], "[ AGENT · Audience Planner ]")
    labeled_box((1360, 180, 1880, 990), TEAL[:3], "[ AGENT · Copywriter ]")
    labeled_box((690, 95, 1290, 1000), AMBER[:3], "[ HUMAN · Founder ]", emphasize=True)
    img.save(ASSETS / "founder_labels_overlay.png")
    print("wrote founder_labels_overlay.png")
    # pre-composite onto the founder reprise frame (boxes baked, stable for push-in)
    frame = ASSETS / "founder_frame.png"
    if frame.exists():
        comp = Image.alpha_composite(Image.open(frame).convert("RGBA"), img)
        comp.convert("RGB").save(ASSETS / "founder_labeled.png")
        print("wrote founder_labeled.png")


if __name__ == "__main__":
    build_diagram()
    build_chat()
    build_deck()
    build_founder_labels()
    print("assets ->", ASSETS)
