# Appendix E – supplementary flow fields (Figure E.1, parts 1–7)

Scripts that compose the ANSYS Fluent exports in `05_CFD_Simulation/ANSYS_Figures/` into the figures of
Appendix E (WC10, 6.0 mm² wire, UID21 = 0.5 m and UID23 = 2.0 m). They only crop, scale, rotate and place
the exports; the image content is not changed. Run each script as

    python <script>.py <ANSYS_Figures folder> <output folder>

| Part | Figure file (`figures/A_appendix/`) | Script |
|---|---|---|
| 1 | `cfd_pressure_full_path_pair.png` | `cfd_full_path_ruler.py` (vertical ruler, 0 m at the lower edge of the inlet pipe) |
| 2 | `cfd_pressure_ls_tube_pair.png` | `cfd_whole_pairs.py` |
| 3 | `cfd_velocity_ferrule_top_pair.png` | `cfd_ferrule_velocity_pairs.py` |
| 4 | `cfd_velocity_ferrule_bottom_pair.png` | `cfd_ferrule_velocity_pairs.py` |
| 5 | `cfd_velocity_launching_station_pair.png` | `cfd_velocity_detail_pairs.py` |
| 6 | `cfd_velocity_silencer_pair.png` | `cfd_ferrule_velocity_pairs.py` |
| 7 | `cfd_wallshear_ferrules.png` | `cfd_wallshear_ferrules_vertical.py` |

`cfd_velocity_detail_pairs.py` holds the shared helpers (legend split, scale-bar measurement, labels); the other
scripts import them, so all five files must stay in the same folder. It also writes a few intermediate
pairs that are not used in the thesis.

Note: in `pressure_autorange_WC10_UID21.png` the legend title was changed from "Total Pressure" to
"Static Pressure" after the author checked in ANSYS that the field is the static pressure; the export as
written by ANSYS is kept on the author's computer as `pressure_autorange_WC10_UID21_legend_as_exported.png`.
