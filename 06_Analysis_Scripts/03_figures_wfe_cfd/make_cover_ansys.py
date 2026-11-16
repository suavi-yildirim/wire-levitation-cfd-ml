"""
Cover image (titelbild) built from the real ANSYS Fluent result.

Source: 05_CFD_Simulation/ANSYS_Figures/velocity_wire_WC10_UID21.png
        (WC10, UID21 = 6.0 mm2, 0.5 m, mdot = 0.005104 kg/s, contour 0-90 m/s)

Method
------
1. The ANSYS contour is decoded back to velocity with its own colour legend.
2. Each of the five wires (10 mm tube, cover geometry of titelbild.pdf)
   gets the ANSYS field mapped onto its own geometry in normalised gap
   coordinates  eta = (r - r_body) / (R_tube - r_body).
3. The velocity is rescaled by continuity at the same mass flow as the ANSYS
   case (constant flow, varying blockage):  u_target = u_ansys * A_gap,s / A_gap,t
   (measured mdot per UID kept in PANELS for reference only).
4. Streamlines are lines of constant stream function in the section plane
   (psi = int u dr), drawn at equal flux fractions on each side.
5. Wire / ferrule surfaces use an ANSYS-like polyhedral surface mesh with the
   shading profile measured from the ANSYS render; the 6.0 mm2 panel uses the
   real ANSYS surface pixels.

Geometry is true scale (1:1 aspect, 10 mm tube = panel width); wire and ferrule
dimensions come from the CFD CAD (04_CAD_Geometry/WC10_UIDxx_AirVolume.step),
tip corners slightly rounded. Panel placement, size and labels are those of the
original titelbild.pdf; each ferrule tip stays at its original position.
The flow disturbance (collar jets, stagnation zones) is scaled with the ferrule
step height relative to the ANSYS ferrule. Colour range 0-80 m/s (ANSYS colormap).
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "05_CFD_Simulation/ANSYS_Figures/velocity_wire_WC10_UID21.png")
OUTDIR = os.path.join(ROOT, "01_Thesis_Latex/Git/6abd2e69062d299b224d6f5b/figures/00_cover")

# ---------------------------------------------------------------- source image
A = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
H_S = A.shape[0]
XW_L, XW_R = 874.0, 1093.0                     # tube walls [px]
XC_S = 0.5 * (XW_L + XW_R)
PXMM = (XW_R - XW_L) / 10.0                    # px per mm (10 mm tube)
Y_COLLAR, Y_TAPER, Y_TIPSTART, Y_TIPEND = 463, 598, 688, 978
MDOT_S = 0.005104
R_TUBE = 5.0

# colour legend: rows 312..894 -> 90 .. 0 m/s
cb_rows = np.arange(312, 895)
LUT = A[cb_rows, 57]
LUT_V = 90.0 * (894 - cb_rows) / (894 - 312)
VMAX = 80.0          # colour range 0-80 m/s (ANSYS colormap, slightly tighter than the 0-90 legend)

# body profile of the source (half widths in px) -----------------------------
def _edges(y):
    r = A[y, int(XW_L) + 3:int(XW_R) - 2]
    if y < Y_COLLAR:
        m = (r[:, 0] > 60) & (r[:, 1] < 40) & (r[:, 2] < 40)        # red wire
        m |= (r.sum(1) < 30)                                         # mesh lines
    else:
        m = (np.abs(r[:, 0] - r[:, 1]) < 25) & (np.abs(r[:, 1] - r[:, 2]) < 25)
    xs = np.where(m)[0]
    if len(xs) == 0:
        return np.nan
    xs = xs + int(XW_L) + 3
    return 0.5 * (xs[-1] - xs[0])
half = np.array([_edges(y) if y < Y_TIPEND else 0.0 for y in range(H_S)])
half[:Y_COLLAR] = np.nanmedian(half[50:Y_COLLAR - 5])
half[Y_COLLAR:Y_TIPEND] = ndimage.median_filter(half[Y_COLLAR:Y_TIPEND], 7)
_hc = np.median(half[Y_COLLAR + 10:Y_TAPER - 10]); _ht = np.median(half[Y_TIPSTART + 20:Y_TIPEND - 20])
half[Y_COLLAR:Y_TAPER] = np.minimum(half[Y_COLLAR:Y_TAPER], _hc + 2)       # clip edge-detection spikes
half[Y_TIPSTART:Y_TIPEND] = np.minimum(half[Y_TIPSTART:Y_TIPEND], _ht + 1)
RS_MM = half / PXMM                            # source body radius per row [mm]
R_COLLAR_S = np.median(RS_MM[Y_COLLAR + 10:Y_TAPER - 10])
R_TIP_S = np.median(RS_MM[Y_TIPSTART + 20:Y_TIPEND - 20])
R_WIRE_S = RS_MM[200]

# decode velocity, fill non-field pixels (bodies, outlines) from neighbours ---
tree = cKDTree(LUT)
dist, idx = tree.query(A.reshape(-1, 3))
V_S = LUT_V[idx].reshape(A.shape[:2])
valid = (dist.reshape(A.shape[:2]) < 45)
yy, xx = np.mgrid[0:A.shape[0], 0:A.shape[1]]
body = np.abs(xx - XC_S) <= half[:, None]
valid &= ~body
valid &= (xx > XW_L + 0.5) & (xx < XW_R - 0.5)
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
V_S = V_S[iy, ix]
V_S = ndimage.gaussian_filter(V_S, 0.8)

# undisturbed reference profiles  g_ref(eta) = V / U_mean  (axisymmetric mean) ---------
def _row_mean(y):
    rb = RS_MM[y] if y < Y_TIPEND else 0.0
    r = np.linspace(rb, R_TUBE, 200)
    v = 0.5 * (np.interp(XC_S - r * PXMM, np.arange(A.shape[1]), V_S[y]) +
               np.interp(XC_S + r * PXMM, np.arange(A.shape[1]), V_S[y]))
    return np.trapezoid(v * r, r) / np.trapezoid(r, r)
UBAR_S = np.array([_row_mean(y) for y in range(H_S)])
UBAR_SM = ndimage.gaussian_filter1d(UBAR_S, 1.5 * PXMM, mode='nearest')   # smooth mean (no seams at steps)
ETA = np.linspace(0, 1, 101)
def _gref(rows, rb):
    out = []
    for y in rows:
        r = rb + ETA * (R_TUBE - rb)
        v = 0.5 * (np.interp(XC_S - r * PXMM, np.arange(A.shape[1]), V_S[y]) +
                   np.interp(XC_S + r * PXMM, np.arange(A.shape[1]), V_S[y]))
        out.append(v / UBAR_S[y])
    return np.mean(out, 0)


# shading profile across a cylinder, measured on the ANSYS wire (red channel)
def _shade_profile():
    rows = A[60:440, int(XC_S - half[200]):int(XC_S + half[200]) + 1, 0]
    prof = np.array([np.percentile(c[c > 20], 70) if (c > 20).any() else np.nan for c in rows.T])
    u = np.linspace(-1, 1, len(prof))
    ok = ~np.isnan(prof)
    p = np.polyfit(u[ok] ** 2, prof[ok] / np.nanmax(prof), 2)
    return lambda s: np.clip(np.polyval(p, np.clip(s, -1, 1) ** 2), 0.25, 1.0)
SHADE = _shade_profile()
GREF_WIRE = _gref(range(20, 160), R_WIRE_S)            # developed annulus profile far upstream
GREF_TUBE = _gref(range(1070, H_S - 2), 0.0)            # developed tube profile far downstream


def _fer_shade_profile():
    """brightness across the ferrule, measured on the ANSYS tip (cell interiors only)."""
    h = int(np.median(half[Y_TIPSTART + 20:Y_TIPEND - 20]))
    rows = A[Y_TIPSTART + 20:Y_TIPEND - 20, int(XC_S - h):int(XC_S + h) + 1].mean(2)
    prof = np.array([np.percentile(c[c > 60], 75) if (c > 60).any() else np.nan for c in rows.T])
    u = np.linspace(-1, 1, len(prof)); ok = ~np.isnan(prof)
    p = np.polyfit(u[ok] ** 2, prof[ok] / 255.0, 2)
    return lambda s: np.clip(np.polyval(p, np.clip(s, -1, 1) ** 2), 0.3, 1.0)
FER_SHADE = _fer_shade_profile()

# ---------------------------------------------------------------- target layout
FIG_W, FIG_H = 16.0 / 2.54 * 72, 255.11810302734375       # pt; width = text width of the thesis (16 cm)
PANEL_W, PANEL_H = 56.5, 236.0
# Panels evenly spread over the full width: first panel at the left edge, last at the right edge,
# so that the image is aligned with the text on the left and centred on the page.
PANEL_X0 = [i * (FIG_W - PANEL_W) / 4 for i in range(5)]
# Panel x0 and ferrule-tip position [pt] from the original titelbild.pdf (placement kept).
# Body dimensions [mm] from the CFD CAD (04_CAD_Geometry/WC10_UIDxx_AirVolume.step):
#   rw wire radius, rc collar radius, rt tip radius,
#   Lc collar length, Lt taper length, Lp tip length (incl. 0.3 mm end fillet)
PANELS = [
    dict(lab="0.5 mm²", uid="01", x0=PANEL_X0[0], tip=200.59, rw=1.050, rc=1.45, rt=0.735,
         Lc=4.20, Lt=2.149, Lp=8.30, col=[(217, 112, 30)]),
    dict(lab="1.0 mm²", uid="05", x0=PANEL_X0[1], tip=180.92, rw=1.200, rc=1.75, rt=0.960,
         Lc=5.00, Lt=2.375, Lp=8.00, col=[(40, 105, 205)]),
    dict(lab="1.5 mm²", uid="09", x0=PANEL_X0[2], tip=212.39, rw=1.375, rc=2.20, rt=1.070,
         Lc=4.30, Lt=3.397, Lp=8.50, col=[(226, 190, 20), (35, 155, 70)]),
    dict(lab="4.0 mm²", uid="17", x0=PANEL_X0[3], tip=192.72, rw=1.975, rc=2.70, rt=1.550,
         Lc=4.70, Lt=3.457, Lp=10.00, col=[(150, 80, 215)]),
    dict(lab="6.0 mm²", uid="21", x0=PANEL_X0[4], tip=208.45, rw=2.250, rc=3.25, rt=1.835,
         Lc=5.70, Lt=4.254, Lp=13.00, col=None),          # real ANSYS surface
]
RES = 8.0                                        # px per pt
K = PANEL_W / 10.0                               # pt per mm, both axes (true aspect)
SRC_LEN = (Y_TIPEND - Y_COLLAR) / PXMM           # ANSYS ferrule length [mm]


def segments(p):
    """True-scale segment boundaries [pt] (CAD lengths), tip end at its original position."""
    y3 = p["tip"]
    y2 = y3 - p["Lp"] * K
    y1 = y2 - p["Lt"] * K
    y0 = y1 - p["Lc"] * K
    return y0, y1, y2, y3


def map_rows(p, y_pt):
    """target row [pt] -> source row [px], target body radius [mm], source radius [mm]"""
    y0, y1, y2, y3 = segments(p)
    s0, s1, s2, s3 = Y_COLLAR, Y_TAPER, Y_TIPSTART, Y_TIPEND
    ys = np.empty_like(y_pt)
    above = y_pt < y0
    ys[above] = s0 - (y0 - y_pt[above]) / K * PXMM
    below = y_pt >= y3
    ys[below] = s3 + (y_pt[below] - y3) / K * PXMM
    for (ta, tb, sa, sb) in [(y0, y1, s0, s1), (y1, y2, s1, s2), (y2, y3, s2, s3)]:
        m = (y_pt >= ta) & (y_pt < tb)
        ys[m] = sa + (y_pt[m] - ta) / (tb - ta) * (sb - sa)
    ys = np.clip(ys, 0, H_S - 1)
    rs = RS_MM[np.floor(ys).astype(int)]          # no blending across the body steps
    # target radius: source profile scaled per segment
    fc = p["rc"] / R_COLLAR_S
    ft = p["rt"] / R_TIP_S
    fw = p["rw"] / R_WIRE_S
    f = np.where(ys < s0, fw, np.where(ys < s1, fc,
                 np.where(ys < s2, fc + (ft - fc) * (ys - s1) / (s2 - s1), ft)))
    rt = np.where(ys >= s3, 0.0, rs * f)
    rt = np.where(ys < s0, rs * fw, rt)
    # rounded bottom corners of the ferrule tip (radius rho)
    y3 = segments(p)[3]
    rho = min(0.5, 0.6 * p["rt"])
    dz = (y_pt - (y3 - rho * K)) / K
    rnd = (dz > 0) & (y_pt < y3)
    rt = np.where(rnd, p["rt"] - rho + np.sqrt(np.clip(rho ** 2 - dz ** 2, 0, None)), rt)
    rt = np.where(y_pt >= y3, 0.0, rt)
    return ys, rt, rs, fc, ft, f


def voronoi_mesh(s, z, h=0.30, w=0.038, aa=0.02, seed=0):
    """polyhedral-looking surface mesh: 1 on cell edges, 0 inside (surface coords, mm)."""
    rng = np.random.default_rng(seed)
    zs = np.arange(z.min() - 2 * h, z.max() + 2 * h, h * 0.866)
    ss = np.arange(s.min() - 2 * h, s.max() + 2 * h, h)
    S, Z = np.meshgrid(ss, zs)
    S = S + (np.arange(len(zs))[:, None] % 2) * h / 2
    pts = np.c_[S.ravel(), Z.ravel()] + rng.normal(0, 0.09 * h, (S.size, 2))
    d, _ = cKDTree(pts).query(np.c_[s.ravel(), z.ravel()], k=2)
    e = np.clip((w - (d[:, 1] - d[:, 0])) / aa + 0.5, 0, 1)
    return e.reshape(s.shape)


def render_panel(p, seed):
    nx, ny = int(round(PANEL_W * RES)), int(round(PANEL_H * RES))
    xp = (np.arange(nx) + 0.5) / RES                # pt from panel left
    yp = (np.arange(ny) + 0.5) / RES                # pt from top
    ys, rt, rs, fc, ft, fsc = map_rows(p, yp)
    xmm = (xp - PANEL_W / 2) / K                    # mm from axis
    X, Y = np.meshgrid(xmm, ys)
    r = np.abs(X)
    inbody = r < rt[:, None]
    # radial breakpoints (target -> source), piecewise linear in r:
    #   wire region : [r_wire, r_collar, R]   (keeps the stagnation zone in front of the collar
    #                                          proportional to the collar step)
    #   ferrule     : [r_body, R]
    #   below tip   : [0, r_tip, R]           (wake scales with the tip diameter)
    rc_s = R_COLLAR_S; rtip_s = R_TIP_S
    rs_src = np.empty((len(ys), 3)); rs_tgt = np.empty((len(ys), 3))
    for i, (y, a_t, a_s) in enumerate(zip(ys, rt, rs)):
        if y < Y_COLLAR:
            rs_tgt[i] = (a_t, rc_s * fc, R_TUBE); rs_src[i] = (a_s, rc_s, R_TUBE)
        elif y < Y_TIPEND:
            rs_tgt[i] = (a_t, 0.5 * (a_t + R_TUBE), R_TUBE); rs_src[i] = (a_s, 0.5 * (a_s + R_TUBE), R_TUBE)
        else:
            rs_tgt[i] = (0.0, rtip_s * ft, R_TUBE); rs_src[i] = (0.0, rtip_s, R_TUBE)
    t0, t1, t2 = (rs_tgt[:, j][:, None] for j in range(3))
    s0, s1, s2 = (rs_src[:, j][:, None] for j in range(3))
    rr = np.maximum(r, t0)
    rsrc = np.where(rr < t1, s0 + (rr - t0) / np.maximum(t1 - t0, 1e-9) * (s1 - s0),
                    s1 + (rr - t1) / np.maximum(t2 - t1, 1e-9) * (s2 - s1))
    xs = XC_S + np.sign(X) * rsrc * PXMM
    V = ndimage.map_coordinates(V_S, [Y, xs], order=1, mode="nearest")
    # Disturbance scaling: V = U_mean * [g_ref(eta) + beta * (g - g_ref(eta))]
    # beta = step height of this ferrule relative to the ANSYS ferrule, so a small
    # collar step gives a weak jet / small stagnation zone (beta = 1 for 6.0 mm2).
    ub = UBAR_SM[np.floor(ys).astype(int)][:, None]
    rt_sm = ndimage.gaussian_filter1d(rt, 1.0 * K * RES, mode="nearest")[:, None]
    eta_t = np.clip((r - rt_sm) / (R_TUBE - rt_sm), 0, 1)
    gref = np.interp(eta_t, ETA, GREF_WIRE)
    b_c = (p["rc"] - p["rw"]) / (R_COLLAR_S - R_WIRE_S)
    b_t = (p["rc"] - p["rt"]) / (R_COLLAR_S - R_TIP_S)
    y_r = Y_TIPEND - 4.0 * PXMM                     # wake: beta -> 1 over the last 4 mm of the tip
    beta = np.where(ys < Y_TAPER, b_c, np.where(ys < Y_TIPSTART,
                    b_c + (b_t - b_c) * (ys - Y_TAPER) / (Y_TIPSTART - Y_TAPER),
                    np.where(ys < y_r, b_t, b_t + (1 - b_t) * np.clip((ys - y_r) / (Y_TIPEND - y_r), 0, 1))))
    beta = ndimage.gaussian_filter1d(beta, 1.0 * K * RES, mode="nearest")
    beta = np.where(ys >= Y_TIPEND - 0.5 * PXMM, 1.0, beta)[:, None]
    V = ub * gref + beta * (V - ub * gref)
    # continuity rescale, same mass flow for every wire (as the ANSYS case):
    # u ~ 1/A_gap ; the factor is smoothed along the axis (flow adapts over ~2 mm)
    A_t = np.pi * (R_TUBE ** 2 - rt ** 2)
    A_s = np.pi * (R_TUBE ** 2 - np.where(ys >= Y_TIPEND, 0, rs) ** 2)
    fac = ndimage.gaussian_filter1d(A_s / A_t, 2.0 * K * RES)
    V = V * fac[:, None]
    # soften the local over-speed at the tip-end corners (thin peak amplified by the remap):
    # blend towards a smoothed field in a small region around each bottom corner
    y3 = segments(p)[3]
    zc = (yp[:, None] - y3) / K                                  # mm from tip end
    dc = np.hypot(zc, r - p["rt"])                               # mm from the corner
    w = 0.85 * np.exp(-0.5 * (dc / 0.55) ** 2)
    Vsm = ndimage.gaussian_filter(V, 0.8 * K * RES)
    V = V - w * np.clip(V - Vsm, 0, None)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(LUT[::-1] / 255.0)
    rgb = cmap(np.clip(V / VMAX, 0, 1))[..., :3]

    # ---- body surface
    if p["col"] is None:      # real ANSYS pixels (geometry identical to source)
        xsb = XC_S + X / fsc[:, None] * PXMM
        src = np.stack([ndimage.map_coordinates(A[..., c], [Y, xsb], order=1) for c in range(3)], -1) / 255
        rgb[inbody] = src[inbody]
    else:
        zmm = yp / K
        Z = np.broadcast_to(zmm[:, None], X.shape)
        RT = np.broadcast_to(rt[:, None], X.shape)
        u = np.clip(X / np.maximum(RT, 1e-6), -1, 1)
        S = np.maximum(RT, 1e-6) * np.arcsin(u)          # arc length on the surface
        mesh = voronoi_mesh(S[inbody], Z[inbody], seed=seed)
        shade = SHADE(u[inbody])
        isw = (Y < Y_COLLAR)[inbody]
        base = np.empty((inbody.sum(), 3))
        wc = np.array(p["col"][0]) / 255.0
        base[:] = wc
        if len(p["col"]) > 1:                             # green stripe (1.5 mm2)
            stripe = np.abs(u[inbody]) < 0.32
            base[stripe] = np.array(p["col"][1]) / 255.0
        base[~isw] = 1.0
        sh = np.where(isw, shade, FER_SHADE(u[inbody]))
        col = base * sh[:, None]
        col = col * (1 - mesh[:, None])                   # black mesh lines as in ANSYS
        rgb[inbody] = col
    # outline (thin black like ANSYS)
    edge = inbody & ~ndimage.binary_erosion(inbody, iterations=2)
    rgb[edge] = 0.05
    return rgb, V, xmm, yp, rt


def streamlines(V, xmm, yp, rt, n=7):
    """Stream function in the section plane psi = int u dr; equal flux fractions per side."""
    lines = []
    for side in (-1, 1):
        m = (side * xmm) > 0
        x = xmm[m] if side > 0 else xmm[m][::-1]
        Vs = V[:, m] if side > 0 else V[:, m][:, ::-1]
        r = np.abs(x)
        q = np.where(r[None, :] >= rt[:, None], Vs, 0.0)
        psi = np.cumsum(q, 1)
        psi /= psi[:, -1:]
        for f in (np.arange(n) + 0.5) / n:
            pos = np.array([np.interp(f, psi[i], r) for i in range(len(yp))])
            pos = ndimage.gaussian_filter1d(pos, 2 * RES)
            lines.append(side * pos)
    return lines


def build(fname):
    fig = plt.figure(figsize=(FIG_W / 72, FIG_H / 72))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W); ax.set_ylim(FIG_H, 0); ax.axis("off")
    for i, p in enumerate(PANELS):
        rgb, V, xmm, yp, rt = render_panel(p, seed=i)
        x0 = p["x0"]
        ax.imshow(rgb, extent=(x0, x0 + PANEL_W, PANEL_H, 0), interpolation="bilinear", zorder=1)
        for L in streamlines(V, xmm, yp, rt):
            xl = x0 + PANEL_W / 2 + L * K
            ax.plot(xl, yp, color="white", lw=0.35, alpha=0.8, zorder=2,
                    solid_capstyle="butt")
        # redraw body on top of streamlines (clip lines at body)
        body = np.zeros(rgb.shape[:2] + (4,))
        X = np.abs(xmm)[None, :]
        ib = X < rt[:, None]
        ib = ndimage.binary_dilation(ib, iterations=1)
        body[..., :3] = rgb
        body[..., 3] = ib
        ax.imshow(body, extent=(x0, x0 + PANEL_W, PANEL_H, 0), interpolation="bilinear", zorder=3)
        # ferrule segment lines (collar|taper, taper|tip) as in the original cover
        y0, y1, y2, y3 = segments(p)
        for yl in (y1, y2):
            j = int(np.clip(yl * RES, 0, len(rt) - 1))
            rr = max(rt[max(j - 2, 0)], rt[min(j + 2, len(rt) - 1)]) * K
            ax.plot([x0 + PANEL_W / 2 - rr, x0 + PANEL_W / 2 + rr], [yl, yl], color="#22262c",
                    lw=0.6, zorder=4, solid_capstyle="butt")
        ax.text(x0 + PANEL_W / 2, 245.4, p["lab"], ha="center", va="center", fontsize=6.4,
                family="DejaVu Sans")
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUTDIR, f"{fname}.{ext}"), dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    print("source radii [mm]: wire %.3f collar %.3f tip %.3f, ferrule length %.2f mm"
          % (R_WIRE_S, R_COLLAR_S, R_TIP_S, SRC_LEN))
    build("titelbild_ansys")
