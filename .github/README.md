# CFD Modeling and Machine-Learning-Based Prediction of Aerodynamic Floating Conditions in Pneumatic Wire-in-Tube Conveying

Master's thesis data and code — Suavi Yildirim, Institute for Factory Automation and Production Systems (FAPS), Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU), 2026.

## Background

The routing of flexible wires is one of the last largely manual steps in control cabinet manufacturing. Pneumatic transport of wires through tubes is investigated as a contact-free alternative. The air pressure and flow rate at which a wire floats in a vertical tube are the minimum aerodynamic requirement of such a system, but they have so far been found by trial for every wire type.

This work combines three parts:

- **Experiments.** A test series on the Wire Floating Experiment (WFE): 794 stable runs of 20 wire types (5 cross-sections, 0.5–6.0 mm²; 4 lengths, 0.5–3.5 m) in tubes of 8 mm (WC08) and 10 mm (WC10) inner diameter. A Tube Flow Analysis (TFA) characterises the pressure losses of the components in the flow path.
- **CFD.** A steady RANS model (ANSYS Fluent, SST k–ω) of the complete flow path. The silencer and start tube are porous zones calibrated from the TFA. The model includes 9 helical variants of one reference wire.
- **Machine learning.** Physics-informed regression (MATLAB Regression Learner) predicts the floating condition of wire types left out of training.

![Research approach](images/research_approach.png)

## Main results

- With the measured inlet pressure imposed, the computed drag force agrees with the wire weight within 20 % for 32 of the 40 configurations after scaling to the measured mass flow rate.
- Skin friction accounts for a median of 61–66 % of the drag. The large pressure forces on the two ferrules largely cancel.
- Moderate helical deformation of the wire changes the drag by less than 2 %.
- For wire types withheld from training, Gaussian process regression predicts flow rate and pressure with mean absolute percentage errors of 7 % and 8 %. That is 1.7 and 1.4 times the repeatability of the experiment. It fails to extrapolate to the largest wire cross-sections.

## Wire Floating Experiment

![WFE hardware](images/wfe_hardware.jpg)

## Repository contents

| Folder | Contents |
|---|---|
| `01_Thesis/PDF/` | The thesis as PDF ([`MA_Yildirim_2026_CFD_ML_Wire_in_Tube_Conveying_public.pdf`](../01_Thesis/PDF/MA_Yildirim_2026_CFD_ML_Wire_in_Tube_Conveying_public.pdf)) |
| `01_Thesis/LaTeX_Source/` | Complete LaTeX source of the thesis (FAPS template). Main file: `FAPS-Thesis.tex`; chapters, appendix, `figures/`, `tables/` and bibliography files (the CV is not included) |
| `03_Experimental_Data/` | Raw WFE run logs `WFE_<UID>_<instance>_<YYYYMMDD>_<HHMM>.csv` sorted by tube and wire type (`01_WFE_Runs/WC08/UIDxx/`, `01_WFE_Runs/WC10/UIDxx/`), silencer-effect runs (`02_WFE_Silencer_Effect/`), TFA runs and processed tables (`03_TFA_Tube_Flow_Analysis/`, see `TFA_WFE_Description.txt`), stable-phase and per-configuration summaries (`04_Summaries/`) |
| `04_CAD_Geometry/` | Air-volume fluid domains as STEP files per wire UID in `WC08/` and `WC10/`; `Helical_Study/` holds the 9 helical variants of UID 18 in WC10 |
| `05_CFD_Simulation/Report_Data/` | Fluent report files per configuration, the CFD master database and validation scripts. The full ANSYS case and data files (about 127 GB) are not included |
| `06_Analysis_Scripts/` | Python scripts: data preparation, statistics, WFE/CFD figures, ML figures, photo straightness. `README.md` and `PLOTTING_SCRIPTS_MAP.md` map every figure to its script and input data |
| `07_Machine_Learning_PIML/` | MATLAB dataset build, training and grouped validation (`MATLAB_PIML/`), ML datasets (`MAT_Dataset_v8/`), evaluation results, and the Python ablation and figure scripts (`Python_ML_Ablation_and_Figures/`) |
| `08_Straightness_Analysis/` | Photo-based wire straightness: pipeline code, extracted centrelines and metrics (raw photos not included) |
| `.github/images/` | Figures used in this README |

## Requirements

- Python 3 with `numpy`, `scipy`, `pandas`, `matplotlib` and `openpyxl`
- MATLAB with the Statistics and Machine Learning Toolbox (for `07_Machine_Learning_PIML/MATLAB_PIML`)
- LaTeX with biber (for the thesis source)

Some scripts still contain absolute paths from the author's machine. Adjust them before running.

## Licence

- **Code** (`.py`, `.m`): [MIT License](../LICENSE)
- **Data, CAD geometries, figures and documentation**: [CC BY 4.0](../LICENSE-DATA.md)

## Citation

If you use this data or code, please cite the thesis. GitHub's "Cite this repository" button gives the reference from [`CITATION.cff`](../CITATION.cff):

> Yildirim, S. (2026). *CFD Modeling and Machine-Learning-Based Prediction of Aerodynamic Floating Conditions in Pneumatic Wire-in-Tube Conveying*. Master's thesis, Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU).
