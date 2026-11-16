"""Part 7 of Appendix E: wall shear stress on the top and bottom ferrule, vertical layout.

Columns: (a) UID21, 0.5 m wire (left) and (b) UID23, 2.0 m wire (right). In each column the top
ferrule is at the top and the bottom ferrule at the bottom; the wire between them is indicated by
light dashed lines and break marks with its length. The exports are rotated clockwise (their y
axis, upwards in the rig, points to the left), cropped to the ferrule with a short piece of wire,
and scaled to the same collar diameter. One common vertical legend (0-90 Pa, from the complete-wire
export) on the left; labels and the axis icon of the original export (rotated with the images) on the right. Only cropping, rotation, scaling and placement.

Usage: python cfd_wallshear_ferrules_vertical.py <ANSYS_Figures folder> <output folder>
"""
import sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
WHITE = (255, 255, 255)
F = lambda s: ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", s)


def trim(im, pad=6, thr=30):
    bg = Image.new("RGB", im.size, WHITE)
    box = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > thr else 0).getbbox()
    return im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad)))


def load(name):
    im = Image.open(f"{SRC}/{name}").convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im)
    d.rectangle((w - 420, 0, w, int(0.15 * h)), fill=WHITE)
    d.rectangle((w - 300, int(0.75 * h), w, h), fill=WHITE)
    return im


def ferrule(name, kind, stub=0.45):
    """Ferrule with a short wire piece, rotated upright. kind: 'top' (tip left) or 'bottom' (tip right)."""
    im = load(name)
    w, h = im.size
    o = trim(im.crop((0, 0, w, int(0.62 * h))), pad=2)
    a = np.asarray(o).astype(int)
    colh = (np.abs(a - 255).sum(2) > 60).sum(0)
    collar = np.where(colh >= 0.93 * colh.max())[0]
    c0, c1 = collar.min(), collar.max()
    if kind == "top":                         # tip ... collar | wire ->
        fl = c1                               # ferrule length (from tip to collar end)
        o = o.crop((0, 0, min(o.width, c1 + int(stub * fl)), o.height))
    else:                                     # <- wire | collar ... tip
        fl = o.width - c0
        o = o.crop((max(0, c0 - int(stub * fl)), 0, o.width, o.height))
    return trim(o, pad=2).rotate(-90, expand=True, fillcolor=WHITE), colh.max()


def wire_edges(im, at):
    """x-range of the wire in row 'at' of an upright ferrule image."""
    row = np.abs(np.asarray(im).astype(int)[at] - 255).sum(1) > 60
    xs = np.where(row)[0]
    return xs.min(), xs.max()


pieces = {}
for uid, top, bot in (("21", "S06_wallsheer_topferrule_WC10_UID21.png", "S06_wallsheer_bottomerrule_WC10_UID21.png"),
                      ("23", "S06_wallsheer_topferrule_WC10_UID23.png", "S06_wallsheer_WC10_UID23.png")):
    t, ct = ferrule(top, "top")
    b, cb = ferrule(bot, "bottom")
    pieces[uid] = [t, ct, b, cb]
ref = pieces["21"][1]                          # collar diameter [px] of the first panel
for uid in pieces:
    t, ct, b, cb = pieces[uid]
    pieces[uid] = [t.resize((round(t.width * ref / ct), round(t.height * ref / ct)), Image.LANCZOS),
                   b.resize((round(b.width * ref / cb), round(b.height * ref / cb)), Image.LANCZOS)]

GAP = 380
labels = {"21": ("(a) UID21, 0.5 m wire", "0.5 m"), "23": ("(b) UID23, 2.0 m wire", "2.0 m")}

# vertical legend (same quantity and range, 0-90 Pa) from the complete-wire export, on the left
fw = load("S06_wallsheer_fullwire_WC10_UID21.png")
fa = np.abs(np.asarray(fw).astype(int) - 255).sum(2) > 60
cnt = fa[:int(0.8 * fw.height), 400:fw.width - 450].sum(1)
wr = np.where(cnt > 300)[0]                                   # rows of the wire, which runs into the legend area
legc = fw.crop((0, int(0.17 * fw.height), 330, int(0.86 * fw.height)))
ImageDraw.Draw(legc).rectangle((180, wr.min() - 12 - int(0.17 * fw.height), 330, wr.max() + 12 - int(0.17 * fw.height)), fill=WHITE)
leg = trim(legc)
leg = leg.resize((round(leg.width * 1.6), round(leg.height * 1.6)), Image.LANCZOS)

# axis icon of the original export, rotated with the images
src = Image.open(f"{SRC}/S06_wallsheer_WC10_UID23.png").convert("RGB")
w, h = src.size
icon = trim(src.crop((w - 320, int(0.83 * h), w - 120, h))).rotate(-90, expand=True, fillcolor=WHITE)
icon = icon.resize((round(icon.width * 2.0), round(icon.height * 2.0)), Image.LANCZOS)

colw = max(max(p[0].width, p[1].width) for p in pieces.values()) + 420   # room for the wire label
lab_w = int(F(56).getlength("ferrule"))
LEFT = leg.width + 30                                          # legend column
RIGHT = max(lab_w, icon.width) + 40                            # label / icon column
H = max(p[0].height for p in pieces.values()) + GAP + max(p[1].height for p in pieces.values()) + 110
TW = int(F(64).getlength("(a) UID21, 0.5 m wire"))          # column title width
PW = max(max(p[0].width, p[1].width) for p in pieces.values())
CX = [LEFT + TW // 2, LEFT + TW // 2 + TW + 80]                # wire centres: close to the legend, titles do not overlap
WL = int(F(52).getlength("wire, 2.0 m"))
xr = CX[1] + PW // 2 + 40 + WL + 90                           # label / icon column right of the second wire label
canvas = Image.new("RGB", (xr + RIGHT, H), WHITE)
d = ImageDraw.Draw(canvas)
for k, uid in enumerate(("21", "23")):
    t, b = pieces[uid]
    cx = CX[k]
    d.text((cx, 45), labels[uid][0], fill=(0, 0, 0), font=F(64), anchor="mm")
    y_t = 110
    canvas.paste(t, (cx - t.width // 2, y_t))
    y_b = y_t + max(p[0].height for p in pieces.values()) + GAP
    canvas.paste(b, (cx - b.width // 2, y_b))
    # wire between the ferrules: light dashed edges, break marks and length
    l1, r1 = wire_edges(t, t.height - 3)
    x_l, x_r = cx - t.width // 2 + l1, cx - t.width // 2 + r1
    y0, y1 = y_t + t.height + 8, y_b - 8
    grey = (170, 170, 170)
    for x in (x_l, x_r):
        for y in range(y0, y1, 26):
            d.line((x, y, x, min(y + 14, y1)), fill=grey, width=3)
    ym = (y0 + y1) // 2
    for dy in (-14, 14):                        # break marks
        d.line((x_l - 22, ym + dy + 10, x_r + 22, ym + dy - 10), fill=(110, 110, 110), width=3)
    d.text((x_r + 40, ym), f"wire, {labels[uid][1]}", fill=(90, 90, 90), font=F(52), anchor="lm")
# right column: "top ferrule", axis icon, "bottom ferrule"
y_mid_t = 110 + max(p[0].height for p in pieces.values()) // 2
y_mid_b = 110 + max(p[0].height for p in pieces.values()) + GAP + max(p[1].height for p in pieces.values()) // 2
d.text((xr, y_mid_t), "top\nferrule", fill=(0, 0, 0), font=F(56), anchor="lm")
d.text((xr, y_mid_b), "bottom\nferrule", fill=(0, 0, 0), font=F(56), anchor="lm")
canvas.paste(icon, (xr + lab_w // 2 - icon.width // 2, (y_mid_t + y_mid_b) // 2 - icon.height // 2))
# legend on the left, vertically centred
canvas.paste(leg, (10, (H - leg.height) // 2))
canvas.save(f"{OUT}/cfd_wallshear_ferrules.png", dpi=(300, 300))
print("Part 7", canvas.size)
