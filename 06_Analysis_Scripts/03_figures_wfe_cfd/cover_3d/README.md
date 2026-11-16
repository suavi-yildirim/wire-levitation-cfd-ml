# 3D cover preview (not used in the thesis yet)

1. `export_textures.py <make_cover_ansys.py> <out>` exports the mid-plane velocity field of each cover panel
   (with streamlines) and the ferrule geometry from `make_cover_ansys.py`.
2. `render_3d.py <out> Cover_3D_preview.png 4800 2700` renders glass tubes, wires with insulation stripes,
   ferrules (coloured plastic collar per DIN 46228, crimped metal sleeve) and the velocity field on the
   axial section with pyvista (pip install pyvista).
