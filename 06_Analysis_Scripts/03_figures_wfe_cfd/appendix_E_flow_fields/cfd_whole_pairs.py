"""Further Appendix E parts: ANSYS exports used whole (legend kept in place), stacked vertically.
Only the Ansys logo and the axis triad are removed; the second panel is scaled to the scale bar of the first.
Usage: python cfd_whole_pairs.py <ANSYS_Figures folder> <output folder>"""
import sys
sys.argv_saved = list(sys.argv)
from PIL import Image, ImageDraw
SRC, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], SRC, OUT]
exec(open(__file__.replace("cfd_whole_pairs.py", "cfd_velocity_detail_pairs.py")).read().split("\npair(")[0])

def whole(name):
    im = Image.open(f"{SRC}/{name}").convert("RGB"); w, h = im.size
    d = ImageDraw.Draw(im)
    d.rectangle((w - 420, 0, w, int(0.15 * h)), fill=WHITE)
    d.rectangle((w - 260, int(0.80 * h), w, h), fill=WHITE)
    return trim(im)

def stack(names, labels, out):
    ims = []
    for n in names:                                   # legend (scaled) left of the content
        leg, c = split(n)
        ims.append(hcat([leg, c], gap=30, valign="center"))
    k0 = bar_px(ims[0])
    for i in range(1, len(ims)):
        k = bar_px(ims[i])
        if k and abs(k0 / k - 1) > 0.005:
            ims[i] = ims[i].resize((round(ims[i].width * k0 / k), round(ims[i].height * k0 / k)), Image.LANCZOS)
    fig = hcat([label(l, im) for l, im in zip(labels, ims)], gap=80, valign="top")   # side by side
    fig.save(f"{OUT}/{out}", dpi=(300, 300)); print(out, fig.size)

L = ["(a) UID21, 0.5 m wire", "(b) UID23, 2.0 m wire"]
stack(["pressure_autorange_WC10_UID21.png", "pressure_autorange_WC10_UID23.png"], ["(a) UID21, 0.5 m wire, static pressure", "(b) UID23, 2.0 m wire, static pressure"], "cfd_pressure_ls_tube_pair.png")
