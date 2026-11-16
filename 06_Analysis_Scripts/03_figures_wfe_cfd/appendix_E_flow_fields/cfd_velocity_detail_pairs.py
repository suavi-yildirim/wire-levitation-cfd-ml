"""Supplementary velocity figures (Appendix E): WC10, 6.0 mm2 wire, UID23 (2.0 m) and UID21 (0.5 m).

Composes pairs of ANSYS Fluent exports from 05_CFD_Simulation/ANSYS_Figures:
    velocity_wire_*      bottom ferrule          -> cfd_velocity_ferrule_bottom_pair.png
    velocity_wiretop_*   top ferrule             -> cfd_velocity_ferrule_top_pair.png
    velocity_ls_*        launching station       -> cfd_velocity_launching_station_pair.png
    velocity_silencer_*  silencer inlet region   -> cfd_velocity_silencer_pair.png

Processing is limited to cropping, scaling and placement; the image content is not changed:
  * the Ansys logo and the axis triad are left out,
  * the colour legend is cut out and placed next to the panels: one shared legend when both
    exports use the same range, otherwise one legend per panel (launching station: the UID21
    export uses 10-90 m/s, the UID23 export 0-90 m/s),
  * the second panel of each pair is rescaled so that its scale bar has the same length in
    pixels as in the first panel (equal geometric scale in both panels).

Usage: python cfd_velocity_detail_pairs.py <ANSYS_Figures folder> <output folder>
"""
import sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
FONT = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
WHITE = (255, 255, 255)
LEGEND_SCALE = 0.8                               # colour legends at 80 % of their exported size


def trim(im, pad=6):
    bg = Image.new("RGB", im.size, WHITE)
    box = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 30 else 0).getbbox()
    return im.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                    min(im.width, box[2] + pad), min(im.height, box[3] + pad)))


def legend_box(im):
    """Legend region (left edge). It ends above the horizontal inlet pipe of the
    launching-station view, which starts at about 84 % of the image height."""
    w, h = im.size
    return (0, int(0.17 * h), 330, int(0.83 * h))


def split(name):
    """-> (legend image, content image) of one export."""
    im = Image.open(f"{SRC}/{name}").convert("RGB")
    w, h = im.size
    lb = legend_box(im)
    legend = trim(im.crop(lb))
    legend = legend.resize((round(legend.width * LEGEND_SCALE), round(legend.height * LEGEND_SCALE)), Image.LANCZOS)
    c = im.copy()
    d = ImageDraw.Draw(c)
    d.rectangle(lb, fill=WHITE)                                  # legend
    d.rectangle((w - 420, 0, w, int(0.15 * h)), fill=WHITE)      # Ansys logo
    d.rectangle((w - 260, int(0.80 * h), w, h), fill=WHITE)      # axis triad
    return legend, trim(c)


def bar_px(im):
    """Length of the black half of the scale bar [px] (longest dark run in the bottom 15 %)."""
    a = np.asarray(im.convert("L"))
    best = 0
    for row in a[int(0.85 * a.shape[0]):]:
        dark = row < 40
        run = cur = 0
        for v in dark:
            cur = cur + 1 if v else 0
            run = max(run, cur)
        best = max(best, run)
    return best


def label(lab, panel):
    tw = int(FONT.getlength(lab)) + 20                 # canvas at least as wide as the label
    W = max(panel.width, tw)
    out = Image.new("RGB", (W, panel.height + 60), WHITE)
    ImageDraw.Draw(out).text((W // 2, 28), lab, fill=(0, 0, 0), font=FONT, anchor="mm")
    out.paste(panel, ((W - panel.width) // 2, 60))
    return out


def hcat(items, gap=50, valign="top"):
    H = max(i.height for i in items)
    W = sum(i.width for i in items) + gap * (len(items) - 1)
    out = Image.new("RGB", (W, H), WHITE)
    x = 0
    for i in items:
        y = {"top": 0, "bottom": H - i.height}.get(valign, (H - i.height) // 2)
        out.paste(i, (x, y))
        x += i.width + gap
    return out


def vcat(items, gap=40):
    W = max(i.width for i in items)
    out = Image.new("RGB", (W, sum(i.height for i in items) + gap * (len(items) - 1)), WHITE)
    y = 0
    for i in items:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def pair(stem, out, shared_legend=True, stacked=False):
    la, a = split(f"{stem}_WC10_UID21.png")   # UID21 left / top
    lb, b = split(f"{stem}_WC10_UID23.png")
    ka, kb = bar_px(a), bar_px(b)
    if kb and ka and abs(ka / kb - 1) > 0.005:
        b = b.resize((round(b.width * ka / kb), round(b.height * ka / kb)), Image.LANCZOS)
    print(f"{stem}: scale bar {ka} px vs {kb} px -> factor {ka / kb:.3f}")
    a, b = label("(a) UID21, 0.5 m wire", a), label("(b) UID23, 2.0 m wire", b)
    if shared_legend:
        fig = hcat([la, hcat([a, b], valign="top")], valign="center")
    else:
        rows = [hcat([la, a], valign="center"), hcat([lb, b], valign="center")]
        fig = vcat(rows, gap=50) if stacked else hcat(rows, gap=80)
    fig.save(f"{OUT}/{out}", dpi=(300, 300))
    print(" ->", out, fig.size)


pair("velocity_wire", "cfd_velocity_ferrule_bottom_pair.png")
pair("velocity_wiretop", "cfd_velocity_ferrule_top_pair.png")
pair("velocity_ls", "cfd_velocity_launching_station_pair.png", shared_legend=False, stacked=True)
pair("velocity_silencer", "cfd_velocity_silencer_pair.png")

# Static pressure on the ferrule surfaces (narrow colour range per export -> one legend per panel)
pair("S07_pressure_bottomferrule_detail", "cfd_pressure_ferrule_bottom_pair.png", shared_legend=False)
pair("S07_pressure_topferrule_detail", "cfd_pressure_ferrule_top_pair.png", shared_legend=False)

# Complete flow path (static pressure), one legend per panel (ranges differ)
pair("pressure_full", "cfd_pressure_full_path_pair.png", shared_legend=False)
