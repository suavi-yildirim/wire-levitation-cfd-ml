"""Parts 3, 4 and 6 of Appendix E: velocity around the top and bottom ferrule and at the silencer, UID21 (a) and UID23 (b).

Both panels are brought to the same geometric scale (scale bars equal). The ANSYS scale bars are
separated from the panels, the two velocity fields are cropped to the same height (top-aligned),
and a single scale bar (0.02 m, from the UID21 export) is placed centred below both panels.
One colour legend (both exports 0-90 m/s) at 80 % size. Only cropping, scaling and placement.

Usage: python cfd_ferrule_velocity_pairs.py <ANSYS_Figures folder> <output folder>
"""
import sys
import numpy as np
from PIL import Image
SRC, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], SRC, OUT]
exec(open(__file__.replace("cfd_ferrule_velocity_pairs.py", "cfd_velocity_detail_pairs.py")).read().split("\npair(")[0])


def split_bar(im):
    """-> (field without the scale bar, scale bar block with its labels)."""
    a = np.asarray(im.convert("L"))
    h = a.shape[0]
    rows = []
    for y in range(int(0.7 * h), h):
        dark = a[y] < 40
        run = cur = 0
        for v in dark:
            cur = cur + 1 if v else 0
            run = max(run, cur)
        if run > 120:
            rows.append(y)
    y0 = min(rows) - 45                      # labels "0" and "0.02 (m)" above the bar
    field = trim(im.crop((0, 0, im.width, y0 - 4)))
    blk = np.asarray(im.crop((0, y0, im.width, h))).copy()
    sat = blk.max(2).astype(int) - blk.min(2).astype(int)
    blk[sat > 40] = 255                      # remove the coloured field behind the bar; keep bar and text
    bar = trim(Image.fromarray(blk))
    return field, bar


def draw_bar(length, metres="0.02 m"):
    """Clean scale bar of the given length [px]: left half black, right half white with outline."""
    f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    W, H = length + 120, 70
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    x0, y0, bh = 20, 40, 14
    d.rectangle((x0, y0, x0 + length, y0 + bh), outline=(0, 0, 0), fill=WHITE, width=2)
    d.rectangle((x0, y0, x0 + length // 2, y0 + bh), fill=(0, 0, 0))
    d.text((x0, y0 - 6), "0", fill=(0, 0, 0), font=f, anchor="mb")
    d.text((x0 + length, y0 - 6), metres, fill=(0, 0, 0), font=f, anchor="mb")
    return trim(im, pad=4)


def ferrule_pair(stem, out, metres=0.02, legend_scale=1.0):
    leg, a = split(f"{stem}_WC10_UID21.png")
    leg = leg.resize((round(leg.width * legend_scale), round(leg.height * legend_scale)), Image.LANCZOS)
    _, b = split(f"{stem}_WC10_UID23.png")
    ka, kb = bar_px(a), bar_px(b)
    b = b.resize((round(b.width * ka / kb), round(b.height * ka / kb)), Image.LANCZOS)
    fa, _ = split_bar(a)
    bar = draw_bar(ka, f"{metres:g} m")      # ka = length of the scale bar [px] in the UID21 export
    fb, _ = split_bar(b)
    H = min(fa.height, fb.height)            # same height, top-aligned
    fa, fb = fa.crop((0, 0, fa.width, H)), fb.crop((0, 0, fb.width, H))
    panels = hcat([label("(a) UID21, 0.5 m wire", fa), label("(b) UID23, 2.0 m wire", fb)], gap=120, valign="top")
    body = vcat([panels, bar], gap=30)
    fig = hcat([leg, body], gap=60, valign="center")
    # centre the scale bar under the panels
    out_im = Image.new("RGB", fig.size, WHITE)
    out_im.paste(leg, (0, (fig.height - leg.height) // 2))
    x0 = leg.width + 60
    out_im.paste(panels, (x0, 0))
    out_im.paste(bar, (x0 + (panels.width - bar.width) // 2, panels.height + 30))
    out_im.save(f"{OUT}/{out}", dpi=(300, 300))
    print(out, out_im.size, "scale factor UID23", round(ka / kb, 3))


ferrule_pair("velocity_wiretop", "cfd_velocity_ferrule_top_pair.png", legend_scale=1.5)
ferrule_pair("velocity_wire", "cfd_velocity_ferrule_bottom_pair.png", legend_scale=1.5)
ferrule_pair("velocity_silencer", "cfd_velocity_silencer_pair.png", metres=0.1, legend_scale=1.5)
