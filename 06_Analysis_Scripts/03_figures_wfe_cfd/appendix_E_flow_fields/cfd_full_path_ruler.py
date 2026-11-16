"""Part 1 of Appendix E: static pressure along the complete flow path, UID21 (a) and UID23 (b),
each panel with its own legend. Both panels are brought to the same scale (ANSYS 1 m scale bars
equal); the horizontal scale bars are replaced by one vertical ruler on the right, placed a little
away from the tube. Only cropping, scaling and placement.

Usage: python cfd_full_path_ruler.py <ANSYS_Figures folder> <output folder>
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
SRC, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], SRC, OUT]
_self = __file__
__file__ = _self.replace("cfd_full_path_ruler.py", "cfd_ferrule_velocity_pairs.py")   # helpers resolve their paths from __file__
exec(open(__file__).read().split("\nferrule_pair(")[0])
__file__ = _self

la, a = split("pressure_full_WC10_UID21.png")
lb, b = split("pressure_full_WC10_UID23.png")
ka, kb = bar_px(a), bar_px(b)                       # length of the 1 m scale bar [px]
b = b.resize((round(b.width * ka / kb), round(b.height * ka / kb)), Image.LANCZOS)
def remove_bar(im):
    """Remove the ANSYS scale bar and its labels (black/white) but keep the coloured flow path next to it."""
    g = np.asarray(im.convert("L")); h = g.shape[0]
    rows = [y for y in range(int(0.7 * h), h) if (g[y] < 40).sum() > 120]
    y0 = min(rows) - 45
    arr = np.asarray(im).copy()
    sub = arr[y0:]
    sat = sub.max(2).astype(int) - sub.min(2).astype(int)
    sub[sat < 40] = 255                          # bar, outline and labels are grey/black/white
    arr[y0:] = sub
    return trim(Image.fromarray(arr))
fa, fb = remove_bar(a), remove_bar(b)
ppm = ka                                            # px per metre after scaling
H = max(fa.height, fb.height)
def bottom_pad(im, h):                              # bottom-aligned: the inlet pipe of both panels at the same height
    out = Image.new("RGB", (im.width, h), WHITE); out.paste(im, (0, h - im.height)); return out
fa, fb = bottom_pad(fa, H), bottom_pad(fb, H)
pa = hcat([la, label("(a) UID21, 0.5 m wire", fa)], gap=40, valign="center")
pb = hcat([lb, label("(b) UID23, 2.0 m wire", fb)], gap=40, valign="center")
panels = hcat([pa, pb], gap=120, valign="top")

# vertical ruler: 0 m at the lowest point of the flow path (inlet pipe), ticks every 0.5 m
f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
top_m = np.floor(fb.height / ppm * 2) / 2
rh = int(top_m * ppm)
rw = 160
ruler = Image.new("RGB", (rw, rh + 40), WHITE)
d = ImageDraw.Draw(ruler)
x0 = 20
y_bot = rh + 20
RC = (70, 70, 70)                                   # dark grey, thin: the ruler should not dominate
d.line((x0, y_bot, x0, y_bot - rh), fill=RC, width=2)
m = 0.0
while m <= top_m + 1e-9:
    y = y_bot - round(m * ppm)
    major = abs(m - round(m)) < 1e-9
    d.line((x0, y, x0 + (22 if major else 12), y), fill=RC, width=2)
    if major:
        d.text((x0 + 32, y), f"{m:.0f} m", fill=RC, font=f, anchor="lm")
    m += 0.5
# place the ruler right of panel (b), 0 m at the level of the inlet pipe, a little away from the tube
GAP_R = 35
W = panels.width + GAP_R + rw
fig = Image.new("RGB", (W, panels.height + 40), WHITE)
fig.paste(panels, (0, 0))
# 0 m tangent to the lower edge of the inlet pipe: lowest coloured row of the panels
arr = np.asarray(panels).astype(int)
pipe_bottom = np.where((arr.max(2) - arr.min(2) > 40).any(1))[0].max()
fig.paste(ruler, (panels.width + GAP_R, pipe_bottom - y_bot))
fig.save(f"{OUT}/cfd_pressure_full_path_pair.png", dpi=(300, 300))
print("Part 1", fig.size, "px/m", ppm, "ruler", top_m, "m")
