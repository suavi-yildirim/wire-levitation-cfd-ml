"""Two-panel figure: effect of helical wire deformation on the CFD aerodynamics (RQ3).

Successor of 03_Experimental_Data/06_Plots/Helical_Deformation_Aerodynamics.png (16 Sep 2026),
whose script was not kept. That PNG combined panels 1 and 2 of Helix_Plots.py
(drag and inlet mass flow vs. number of helix revolutions, revolutions 0-5).

IMPORTANT - the old PNG cannot be reproduced from the data now on the drive:
  * it shows revolutions 2 and 4, but only Rev 1, 3, 5 cases exist
    (05_CFD_Simulation/Report_Data/Helix_Dia*_Rev*_WC10_UID18, also Helical.zip);
  * its mass flow varies (8.17e-3 ... 8.58e-3 kg/s), whereas all current cases run with a
    fixed inlet mass flow (8.576e-3 kg/s), i.e. a mass-flow-inlet boundary condition.
So this script plots the current case set. With a fixed mass flow, panel (b) shows the
inlet static pressure, which is the response quantity. If the mass flow does vary in a future
case set, panel (b) switches back to mass flow automatically.

Inputs (columns of sheet 'Summary_Results', final iteration of each case)
  05_CFD_Simulation/Report_Data/Master_Helix_CFD_Database.xlsx  (9 helix cases)
  05_CFD_Simulation/Report_Data/Master_CFD_Database.xlsx        (straight reference WC10_UID18 = Rev 0)
  Columns: Simulation_ID, Helix_Dia, Helix_Rev, total-wire-drag-force (N),
           pressure-inlet (Pa, gauge), mass-flow-inlet (kg/s)
  Both workbooks are written by 03_figures_wfe_cfd/cfd_helix_master_database.py and cfd_master_database.py.

Output: fig_helical_aerodynamics.pdf/.png and helical_aerodynamics_table.csv in --out.

Usage: python fig_helical_aerodynamics.py [--report-data DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # .../MA_YILDIRIM
DEF_RD = ROOT / "05_CFD_Simulation/Report_Data"
DEF_OUT = ROOT / "06_Analysis_Scripts/output/06_Plots_regenerated"
REF_ID = "WC10_UID18"

INK, INK2, GRID = "#1A1A1A", "#4D4D4D", "#E3E3E3"
# ordinal ramp for helix amplitude (FAPS green ramp of style.py, light -> dark)
DIA_COLOR = {1.0: "#9DBE6C", 1.5: "#668E23", 2.0: "#2E440B"}
DIA_MARKER = {1.0: "o", 1.5: "s", 2.0: "D"}
CM = 1 / 2.54
TEXTWIDTH = 16.0 * CM


def apply_style():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Latin Modern Roman", "CMU Serif", "DejaVu Serif"],
        "mathtext.fontset": "cm", "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5, "legend.title_fontsize": 7.5,
        "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": INK2,
        "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
        "grid.color": GRID, "grid.linewidth": 0.45, "lines.linewidth": 1.3, "lines.markersize": 4.5,
        "legend.frameon": False, "savefig.dpi": 400, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02, "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def load(rd: Path) -> pd.DataFrame:
    helix = pd.read_excel(rd / "Master_Helix_CFD_Database.xlsx", sheet_name="Summary_Results")
    straight = pd.read_excel(rd / "Master_CFD_Database.xlsx", sheet_name="Summary_Results")
    ref = straight[straight["Simulation_ID"] == REF_ID].iloc[0]
    rows = []
    for dia in sorted(helix["Helix_Dia"].unique()):
        r = ref.copy(); r["Helix_Dia"] = dia; r["Helix_Rev"] = 0; r["Simulation_ID"] = f"{REF_ID} (straight)"
        rows.append(r)
    df = pd.concat([pd.DataFrame(rows), helix], ignore_index=True)
    df["Helix_Rev"] = df["Helix_Rev"].astype(float)
    df["mdot"] = df["mass-flow-inlet"].abs()
    df["p_in_kPa"] = df["pressure-inlet"] / 1e3
    df["F_D"] = df["total-wire-drag-force"]
    return df.sort_values(["Helix_Dia", "Helix_Rev"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report-data", type=Path, default=DEF_RD)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    apply_style()

    df = load(a.report_data)
    cols = ["Simulation_ID", "Helix_Dia", "Helix_Rev", "F_D", "p_in_kPa", "mdot"]
    df[cols].to_csv(a.out / "helical_aerodynamics_table.csv", index=False)
    print(df[cols].to_string(index=False))

    mdot_spread = (df["mdot"].max() - df["mdot"].min()) / df["mdot"].mean()
    fixed_mdot = mdot_spread < 1e-3
    print(f"Relative mass-flow spread: {mdot_spread:.2e} -> panel (b) = "
          f"{'inlet pressure (mass flow fixed)' if fixed_mdot else 'mass flow'}")

    fig, axes = plt.subplots(1, 2, figsize=(TEXTWIDTH, TEXTWIDTH * 0.4))
    panels = [("F_D", "Total wire drag force $F_\\mathrm{D}$ (N)", "a")]
    panels.append(("p_in_kPa", "Inlet static pressure $p_\\mathrm{in}$ (kPa)", "b") if fixed_mdot
                  else ("mdot", "Inlet mass flow $\\dot{m}$ (kg/s)", "b"))
    for ax, (col, ylabel, letter) in zip(axes, panels):
        for dia, d in df.groupby("Helix_Dia"):
            ax.plot(d["Helix_Rev"], d[col], color=DIA_COLOR.get(dia, INK2), marker=DIA_MARKER.get(dia, "o"),
                    mec="white", mew=0.6, label=f"{dia:.1f} mm")
        ax.set_xlabel("Number of helix revolutions $n_\\mathrm{rev}$")
        ax.set_ylabel(ylabel)
        ax.set_xticks(sorted(df["Helix_Rev"].unique()))
        ax.set_title(f"$\\bf{{({letter})}}$", loc="left")
    axes[1].legend(title="Helix amplitude", loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(a.out / f"fig_helical_aerodynamics.{ext}")
    print("  wrote fig_helical_aerodynamics.pdf/.png")


if __name__ == "__main__":
    main()
