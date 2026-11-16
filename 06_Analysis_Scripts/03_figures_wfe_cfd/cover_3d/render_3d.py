"""3D rendering of the cover: five glass tubes (10 mm inner diameter) with wire and bottom ferrule,
and the mid-plane velocity field (textures exported from the 2D cover) on the axial section.

Units: mm. Usage: python render_3d.py <folder with tex_*.png and geometry.json> <output.png> [width height]
"""
import json, sys
import numpy as np
import pyvista as pv
from PIL import Image

D, OUT = sys.argv[1], sys.argv[2]
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (4800, 2700)
g = json.load(open(f"{D}/geometry.json"))
K, PW, PH = g["K_pt_per_mm"], g["panel_w_pt"], g["panel_h_pt"]
HZ = PH / K                     # height of the shown section [mm]
R_IN, R_OUT = 5.0, 6.2          # glass tube
SPACING = 17.5                  # tube spacing [mm] (as on the cover)
z = lambda y_pt: (PH - y_pt) / K

# Wire insulation: base colour and optional longitudinal stripes (centre angle [deg], half width [deg], colour)
INSUL = {"01": ((228, 110, 30), []),                                            # 0.5 mm2 orange
         "05": ((30, 85, 190), [(-105, 11, (245, 245, 245))]),                 # 1.0 mm2 blue with white stripe (facing the camera)
         "09": ((235, 200, 30), [(-60, 32, (35, 145, 65)), (120, 32, (35, 145, 65))]),  # 1.5 mm2 green-yellow
         "17": ((135, 85, 195), []),                                          # 4.0 mm2 purple
         "21": ((205, 25, 30), [])}                                           # 6.0 mm2 red
# Plastic collar of the wire-end ferrule, colour code DIN 46228 (as on the test specimens)
COLLAR = {"01": (238, 238, 234), "05": (205, 30, 35), "09": (28, 28, 30), "17": (150, 152, 158), "21": (28, 28, 30)}


def revolve(profile, x0, res=160):
    """Surface of revolution about the vertical axis through (x0, 0); profile = [(r, z), ...]."""
    pts = np.array([[r, 0.0, zz] for r, zz in profile])
    line = pv.lines_from_points(pts)
    surf = line.extrude_rotate(resolution=res, rotation_axis=(0, 0, 1), capping=False)
    surf = surf.translate((x0, 0, 0), inplace=False)
    return surf.compute_normals(split_vertices=False, consistent_normals=True)


def crimped_sleeve(x0, z_top, z_end, r, n_seg=7, n_th=240, n_z=900):
    """Metal sleeve of a wire end ferrule after crimping with a square (4-mandrel) crimp tool:
    rounded-square pressed cross-section in the crimp zone, round near the collar, n_seg shallow
    die marks along the crimp, slight flare at the open end. Rounded lower end."""
    rho = 0.0                                              # open, flat end
    zz = np.linspace(z_top, z_end + rho, n_z)
    L = z_top - (z_end + rho)
    t = (z_top - zz) / L                                   # 0 at the collar, 1 at the tip
    th = np.linspace(0, 2 * np.pi, n_th)
    # crimp zone from 12 % to 96 % of the length, smooth transitions
    cz = np.clip((t - 0.06) / 0.10, 0, 1) * np.clip((0.99 - t) / 0.05, 0, 1)
    cz = cz * cz * (3 - 2 * cz)
    # rounded square (superellipse) with the same perimeter scale, rotated 45 deg towards the camera
    p = 4.0
    c, s_ = np.abs(np.cos(th + np.pi / 4)), np.abs(np.sin(th + np.pi / 4))
    sq = (c ** p + s_ ** p) ** (-1 / p)
    sq = sq / sq.mean()
    # shallow die marks: n_seg flat bands separated by narrow, low ridges
    seg = np.clip((t - 0.12) / 0.84, 0, 1) * n_seg
    f = seg - np.floor(seg)
    ridge = np.exp(-((np.minimum(f, 1 - f)) / 0.05) ** 2) * cz
    rz = r * (1 - 0.10 * cz + 0.025 * ridge)
    R = rz[:, None] * (1 + (sq[None, :] - 1) * 0.85 * cz[:, None])
    # tiny random surface waviness (pressed sheet metal), deterministic
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 1, (n_z // 30 + 2, n_th // 20 + 2))
    from scipy.ndimage import zoom
    noise = zoom(noise, (n_z / noise.shape[0], n_th / noise.shape[1]), order=3)[:n_z, :n_th]
    noise[:, -1] = noise[:, 0]
    R = R * (1 + 0.006 * noise * cz[:, None])
    X = x0 + R * np.cos(th)[None, :]; Y = R * np.sin(th)[None, :]; Z = np.repeat(zz[:, None], n_th, 1)
    body = pv.StructuredGrid(X, Y, Z).extract_surface().compute_normals(split_vertices=False, consistent_normals=True)
    # open lower end: sleeve wall (annulus) and the ends of the copper strands, which stick out a little
    rr = rz[-1]
    ring = pv.Disc(center=(x0, 0, z_end), inner=0.82 * rr, outer=rr, normal=(0, 0, -1), c_res=n_th)
    rs = 0.11 * rr                                         # strand radius
    rng2 = np.random.default_rng(7)
    pts = []
    for k in range(-8, 9):
        for j in range(-8, 9):
            px, py = (j + 0.5 * (k % 2)) * 2.05 * rs, k * 1.78 * rs
            if np.hypot(px, py) < 0.80 * rr - rs:
                pts.append((px, py))
    strands = pv.MultiBlock()
    for px, py in pts:
        stick = 0.55 + 0.45 * rng2.random()                # protrusion below the sleeve end [mm]
        tilt = rng2.normal(0, 0.06, 2) + 0.10 * np.array([px, py]) / rr
        c = pv.Cylinder(center=(x0 + px + tilt[0] * stick / 2, py + tilt[1] * stick / 2, z_end - stick / 2 + 0.2),
                        direction=(tilt[0], tilt[1], 1), radius=rs * 0.95, height=stick + 0.4, resolution=24)
        strands.append(c)
    return body, ring, strands.combine().extract_surface()


def studio_cubemap(folder, n=256):
    """Soft studio environment (bright ceiling, two softboxes, grey floor) for image-based lighting."""
    import os
    from PIL import Image as I
    names = ["posx", "negx", "posy", "negy", "posz", "negz"]
    u = np.linspace(-1, 1, n)
    U, V = np.meshgrid(u, -u)
    dirs = {"posx": (np.ones_like(U), V, -U), "negx": (-np.ones_like(U), V, U), "posy": (U, np.ones_like(U), -V),
            "negy": (U, -np.ones_like(U), V), "posz": (U, V, np.ones_like(U)), "negz": (-U, V, -np.ones_like(U))}
    paths = []
    for k in names:
        x, y, z = dirs[k]
        nrm = np.sqrt(x * x + y * y + z * z); x, y, z = x / nrm, y / nrm, z / nrm
        up = y                                             # VTK cube map: +y is up
        v = 0.30 + 0.40 * np.clip(up, -1, 1)
        v += 1.4 * np.exp(-((x + 0.6) ** 2 + (up - 0.3) ** 2 + (z + 0.6) ** 2) / 0.08)   # key softbox
        v += 0.8 * np.exp(-((x - 0.8) ** 2 + (up - 0.1) ** 2 + (z + 0.3) ** 2) / 0.05)   # fill softbox
        v = np.clip(v, 0, 1)
        img = (np.stack([v * 0.97, v * 0.98, v], -1) * 255).astype(np.uint8)
        pth = os.path.join(folder, f"env_{k}.png"); I.fromarray(img).save(pth); paths.append(pth)
    return pv.cubemap_from_filenames(paths)


pl = pv.Plotter(off_screen=True, window_size=(W, H), lighting="none")
pl.set_background("white")
pl.enable_anti_aliasing("ssaa")
pl.enable_depth_peeling(number_of_peels=12)
import tempfile
pl.set_environment_texture(studio_cubemap(tempfile.mkdtemp()))

for i, p in enumerate(g["panels"]):
    x0 = (i - 2) * SPACING
    zc, zt, zp, ze = z(p["y_collar_top"]), z(p["y_taper_top"]), z(p["y_tip_top"]), z(p["y_tip_end"])
    rw, rc, rt = p["rw"], p["rc"], p["rt"]
    # --- velocity field on the axial section (y = 0 plane); the region of the solid wire is made
    #     transparent, so that the section ends at the 3D wire surface
    img = np.array(Image.open(f"{D}/tex_{i}.png").convert("RGBA"))
    hp, wp = img.shape[:2]
    zz = HZ * (1 - (np.arange(hp) + 0.5) / hp)                      # z of each texture row [mm]
    xx = (np.arange(wp) + 0.5) / wp * 2 * R_IN - R_IN               # x of each texture column [mm]
    rbody = np.interp(zz, [ze, ze + 0.001, zp, zt, zc, zc + 0.001, HZ + 1], [0, rt, rt, rc, rc, rw, rw], left=0, right=rw)
    img[np.abs(xx)[None, :] < rbody[:, None], 3] = 0
    tex = pv.Texture(img)                                           # pyvista maps array row 0 to the top (checked visually)
    quad = pv.PolyData(np.array([[x0 - R_IN, 0, 0], [x0 + R_IN, 0, 0], [x0 + R_IN, 0, HZ], [x0 - R_IN, 0, HZ]], float), faces=[4, 0, 1, 2, 3])
    quad.active_texture_coordinates = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    pl.add_mesh(quad, texture=tex, lighting=False)
    # --- wire with bottom ferrule (solid of revolution)
    # wire insulation with longitudinal stripes (colours per vertex, by angle around the axis)
    wire = revolve([(rw, HZ + 0.5), (rw, zc)], x0, res=360)
    base, stripes = INSUL[p["uid"]]
    ang = np.degrees(np.arctan2(wire.points[:, 1], wire.points[:, 0] - x0))
    rgb = np.tile(np.array(base, float), (wire.n_points, 1))
    for c, hw, sc in stripes:
        d = (ang - c + 180) % 360 - 180
        rgb[np.abs(d) < hw] = sc
    wire["rgb"] = rgb.astype(np.uint8)
    pl.add_mesh(wire, scalars="rgb", rgb=True, ambient=0.2, diffuse=0.85, specular=0.35, specular_power=25, smooth_shading=True)
    # plastic collar (cylinder + funnel) in the colour code of the cross-section, matt plastic
    collar = revolve([(rw, zc), (rc, zc), (rc, zt), (rt, zp)], x0, res=200)
    pl.add_mesh(collar, color=np.array(COLLAR[p["uid"]]) / 255, ambient=0.22, diffuse=0.8, specular=0.25,
                specular_power=15, smooth_shading=True)
    # metal sleeve, crimped: 7 segments, pressed cross-section; tin-plated copper, shiny metal
    body, ring, strands = crimped_sleeve(x0, zp, ze, rt)
    for part in (body, ring):
        pl.add_mesh(part, color=(0.86, 0.86, 0.85), pbr=True, metallic=1.0, roughness=0.25, smooth_shading=True)
    pl.add_mesh(strands, color=(0.95, 0.60, 0.38), pbr=True, metallic=1.0, roughness=0.22)      # bare copper
    # --- glass tube (inner and outer wall), slightly blue tint
    tube_o = revolve([(R_OUT, -0.5), (R_OUT, HZ + 0.5)], x0, res=200)
    tube_i = revolve([(R_IN, -0.5), (R_IN, HZ + 0.5)], x0, res=200)
    for t in (tube_i, tube_o):
        pl.add_mesh(t, color=(0.85, 0.92, 0.97), opacity=0.07, ambient=0.05, diffuse=0.3,
                    specular=1.0, specular_power=120, smooth_shading=True)
    # rims of the glass tube at the top and bottom (visible edges, as on a real tube)
    for zr in (-0.5, HZ + 0.5):
        rim = pv.Disc(center=(x0, 0, zr), inner=R_IN, outer=R_OUT, normal=(0, 0, 1), c_res=200)
        pl.add_mesh(rim, color=(0.75, 0.84, 0.90), opacity=0.55, specular=1.0, specular_power=80)

# lighting: key, fill and rim light
pl.add_light(pv.Light(position=(-60, -120, 90), focal_point=(0, 0, HZ / 2), intensity=1.0))
pl.add_light(pv.Light(position=(80, -90, 30), focal_point=(0, 0, HZ / 2), intensity=0.55))
pl.add_light(pv.Light(position=(0, 120, 60), focal_point=(0, 0, HZ / 2), intensity=0.5))
pl.add_light(pv.Light(light_type="headlight", intensity=0.25))
pl.add_light(pv.Light(position=(-150, -60, 20), focal_point=(0, 0, HZ / 3), intensity=0.45))   # grazing light: metal highlights on the crimp segments

pl.camera.focal_point = (0, 0, HZ / 2 - 1)
pl.camera.position = (-60, -330, HZ / 2 + 110)          # far away: little perspective distortion
pl.camera.up = (0, 0, 1)
pl.camera.view_angle = 12
pl.screenshot(OUT, transparent_background=False)
# crop the white border and fit to the cover aspect ratio (16 cm x 9 cm)
from PIL import ImageChops
im = Image.open(OUT).convert("RGB")
box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 8 else 0).getbbox()
im = im.crop(box)
ar = 16.0 / 9.0
w, h = im.size
if w / h < ar:
    nw = round(h * ar); c = Image.new("RGB", (nw, h), "white"); c.paste(im, ((nw - w) // 2, 0)); im = c
else:
    nh = round(w / ar); c = Image.new("RGB", (w, nh), "white"); c.paste(im, (0, (nh - h) // 2)); im = c
im.save(OUT)
print("saved", OUT, (W, H))
