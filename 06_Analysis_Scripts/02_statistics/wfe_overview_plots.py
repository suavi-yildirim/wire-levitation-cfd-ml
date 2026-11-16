"""WFE overview plots of the stable-phase summary (all runs, both tubes).

Reproduces the four early overview figures in 03_Experimental_Data/06_Plots (July 2026),
for which no script had been kept, in the thesis figure style and as vector PDF + PNG:

  plot_stabilization_trend_share       share of runs by Final_Trend (wire_rises / wire_drops / unknown)
  plot_section_pressure_boxplot        stable pressure per cross-section (box plot)
  plot_length_vs_pressure_with_error_band   mean stable pressure vs. wire length, +/- 1 SD band per section
  plot_pressure_vs_flow_by_section     stable pressure vs. stable flow, coloured by section, OLS line + 95 % CI

Input
  03_Experimental_Data/04_Summaries/Stable_Phase_Summary__SystemStable_TRUE.csv
  (written by 01_data_preparation/process_data.py)
  Columns used: WIRE_section, WIRE_lenght (m), Tube_Diameter, Final_Trend,
                Pressure_Stable_Average (mbar), Flow_Stable_Average (Nm^3/h)

Filter: rows with WIRE_section in {0.5, 1.0, 1.5, 4.0, 6.0} mm^2 (drops the single 0.0 test row).
Both tubes (WC08 and WC10) are pooled, as in the original July figures.

Usage
  python wfe_overview_plots.py [--data CSV] [--out DIR]
Defaults resolve relative to the MA_YILDIRIM drive layout, so it runs from any working directory.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # .../MA_YILDIRIM
DEF_DATA = ROOT / "03_Experimental_Data/04_Summaries/Stable_Phase_Summary__SystemStable_TRUE.csv"
DEF_OUT = ROOT / "06_Analysis_Scripts/output/06_Plots_regenerated"

COL_P = "Pressure_Stable_Average (mbar)"
COL_Q = "Flow_Stable_Average (Nm^3/h)"
COL_S = "WIRE_section"
COL_L = "WIRE_lenght (m)"          # sic, spelling of the source file
COL_T = "Final_Trend"

# Same colour system as WFE_thesis_figures/code/style.py (wire insulation colours, CVD-checked)
SECTIONS = [0.5, 1.0, 1.5, 4.0, 6.0]
SEC_COLOR = {0.5: "#E86A17", 1.0: "#2F7DD9", 1.5: "#DDAA00", 4.0: "#7A3CB8", 6.0: "#A8102F"}
SEC_MARKER = {0.5: "o", 1.0: "s", 1.5: "^", 4.0: "D", 6.0: "v"}
TREND_COLOR = {"wire_rises": "#2A5C9E", "wire_drops": "#668E23", "unknown": "#A7B3C0"}
TREND_LABEL = {"wire_rises": "Wire rises", "wire_drops": "Wire drops", "unknown": "Undetermined"}
INK, INK2, GRID = "#1A1A1A", "#4D4D4D", "#E3E3E3"
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


def sec_label(s: float) -> str:
    return f"{s:.1f} mm$^2$"


def save(fig, out: Path, name: str):
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}")
    plt.close(fig)
    print(f"  wrote {name}.pdf/.png")


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    n0 = len(df)
    df = df[df[COL_S].isin(SECTIONS)].copy()
    print(f"Loaded {path.name}: {n0} rows, {len(df)} after section filter")
    return df


def fig_trend_share(df, out):
    counts = df[COL_T].value_counts().reindex(["wire_rises", "wire_drops", "unknown"]).fillna(0).astype(int)
    n = counts.sum()
    print("Final_Trend shares:", {k: f"{v} ({100 * v / n:.1f} %)" for k, v in counts.items()})
    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.5, TEXTWIDTH * 0.42))
    wedges, _ = ax.pie(counts.values, colors=[TREND_COLOR[k] for k in counts.index], startangle=90,
                       counterclock=False, wedgeprops=dict(linewidth=0.8, edgecolor="white"))
    for w, (k, v) in zip(wedges, counts.items()):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        ax.text(0.68 * np.cos(ang), 0.68 * np.sin(ang), f"{100 * v / n:.1f} %\n($n$ = {v})",
                ha="center", va="center", fontsize=7.5, color="white" if k != "unknown" else INK)
    ax.legend(wedges, [TREND_LABEL[k] for k in counts.index], loc="center left",
              bbox_to_anchor=(1.0, 0.5), title=f"Final trend ($N$ = {n})")
    ax.set_aspect("equal")
    save(fig, out, "plot_stabilization_trend_share")


def fig_section_box(df, out):
    data = [df.loc[df[COL_S] == s, COL_P].values for s in SECTIONS]
    fig, ax = plt.subplots(figsize=(TEXTWIDTH, TEXTWIDTH * 0.45))
    bp = ax.boxplot(data, patch_artist=True, widths=0.55, whis=1.5,
                    medianprops=dict(color=INK, lw=1.0), whiskerprops=dict(color=INK2, lw=0.7),
                    capprops=dict(color=INK2, lw=0.7),
                    flierprops=dict(marker="o", ms=2.5, mfc="none", mec=INK2, mew=0.5))
    for patch, s in zip(bp["boxes"], SECTIONS):
        patch.set_facecolor(SEC_COLOR[s]); patch.set_alpha(0.75); patch.set_edgecolor(INK2); patch.set_linewidth(0.7)
    ax.set_xticks(range(1, len(SECTIONS) + 1), [sec_label(s) for s in SECTIONS])
    ax.set_xlabel("Wire cross-section $A_\\mathrm{w}$")
    ax.set_ylabel("Stable static pressure $p$ (mbar)")
    ax.grid(axis="x", visible=False)
    for i, d in enumerate(data, 1):
        ax.text(i, 1.0, f"$n$ = {len(d)}", ha="center", va="bottom", fontsize=7, color=INK2,
                transform=ax.get_xaxis_transform())
    save(fig, out, "plot_section_pressure_boxplot")


def fig_length_band(df, out):
    g = df.groupby([COL_S, COL_L])[COL_P].agg(["mean", "std", "count"]).reset_index()
    g.to_csv(out / "length_vs_pressure_mean_sd.csv", index=False)
    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.78, TEXTWIDTH * 0.5))
    for s in SECTIONS:
        d = g[g[COL_S] == s].sort_values(COL_L)
        c = SEC_COLOR[s]
        ax.fill_between(d[COL_L], d["mean"] - d["std"], d["mean"] + d["std"], color=c, alpha=0.12, lw=0)
        ax.plot(d[COL_L], d["mean"], color=c, marker=SEC_MARKER[s], mec="white", mew=0.6, label=sec_label(s))
    ax.set_xticks([0.5, 1.0, 2.0, 3.5])
    ax.set_xlabel("Wire length $L$ (m)")
    ax.set_ylabel("Stable static pressure $p$ (mbar)")
    ax.set_ylim(bottom=0)
    ax.legend(title="Cross-section (mean $\\pm$ 1 SD)", loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, out, "plot_length_vs_pressure_with_error_band")


def fig_pressure_flow(df, out):
    x, y = df[COL_Q].to_numpy(), df[COL_P].to_numpy()
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    s2 = resid @ resid / (n - k)
    r2 = 1 - (resid @ resid) / np.sum((y - y.mean()) ** 2)
    xg = np.linspace(x.min(), x.max(), 200)
    Xg = np.column_stack([np.ones_like(xg), xg])
    se = np.sqrt(np.einsum("ij,jk,ik->i", Xg, s2 * np.linalg.inv(X.T @ X), Xg))
    from scipy import stats
    t = stats.t.ppf(0.975, n - k)
    print(f"OLS p = {beta[0]:.1f} + {beta[1]:.2f} Q  (mbar, Nm^3/h), R^2 = {r2:.3f}, n = {n}")

    fig, ax = plt.subplots(figsize=(TEXTWIDTH * 0.78, TEXTWIDTH * 0.5))
    for s in SECTIONS:
        d = df[df[COL_S] == s]
        ax.scatter(d[COL_Q], d[COL_P], s=14, color=SEC_COLOR[s], marker=SEC_MARKER[s],
                   edgecolor="white", linewidth=0.4, alpha=0.9, label=sec_label(s), zorder=3)
    ax.fill_between(xg, Xg @ beta - t * se, Xg @ beta + t * se, color=INK2, alpha=0.15, lw=0, zorder=2)
    ax.plot(xg, Xg @ beta, color=INK, ls="--", lw=1.0, zorder=4,
            label=f"OLS fit ($R^2$ = {r2:.3f})")
    ax.set_xlabel("Stable volume flow $\\dot{V}_\\mathrm{N}$ (Nm$^3$/h)")
    ax.set_ylabel("Stable static pressure $p$ (mbar)")
    ax.set_ylim(bottom=0)
    ax.legend(title="Cross-section", loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, out, "plot_pressure_vs_flow_by_section")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=DEF_DATA)
    ap.add_argument("--out", type=Path, default=DEF_OUT)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    apply_style()
    df = load(a.data)
    fig_trend_share(df, a.out)
    fig_section_box(df, a.out)
    fig_length_band(df, a.out)
    fig_pressure_flow(df, a.out)


if __name__ == "__main__":
    main()
