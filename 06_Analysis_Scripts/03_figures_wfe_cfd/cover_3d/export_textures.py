"""Export the mid-plane velocity field of each cover panel (with streamlines) as a texture,
plus the ferrule geometry, for the 3D cover rendering.

Uses the functions of make_cover_ansys.py (imported, its __main__ block is not run).
Output: tex_<i>.png (field, 10 mm wide x PANEL_H tall, the body region left as it is - it is
hidden by the 3D wire) and geometry.json.
"""
import importlib.util, json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT, OUT = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("cover", SCRIPT)
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

geo = {"K_pt_per_mm": cv.K, "panel_w_pt": cv.PANEL_W, "panel_h_pt": cv.PANEL_H, "panels": []}
for i, p in enumerate(cv.PANELS):
    rgb, V, xmm, yp, rt = cv.render_panel(p, seed=i)
    h_in = cv.PANEL_H / 72 * 3          # render at 3x the cover size
    w_in = cv.PANEL_W / 72 * 3
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, cv.PANEL_W); ax.set_ylim(cv.PANEL_H, 0)
    ax.imshow(rgb, extent=(0, cv.PANEL_W, cv.PANEL_H, 0), interpolation="bilinear")
    for L in cv.streamlines(V, xmm, yp, rt):
        ax.plot(cv.PANEL_W / 2 + L * cv.K, yp, color="white", lw=0.5, alpha=0.85)
    fig.savefig(os.path.join(OUT, f"tex_{i}.png"), dpi=600)
    plt.close(fig)
    y0, y1, y2, y3 = cv.segments(p)
    geo["panels"].append(dict(lab=p["lab"], uid=p["uid"], rw=p["rw"], rc=p["rc"], rt=p["rt"],
                              y_collar_top=y0, y_taper_top=y1, y_tip_top=y2, y_tip_end=y3,
                              col=p["col"]))
    print("panel", i, p["lab"])
json.dump(geo, open(os.path.join(OUT, "geometry.json"), "w"), indent=1)
print("done")
