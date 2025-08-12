# LAMP-IPA

## Overview
The IPA GUI is an interactive python based application that aims to improve the useability of the IPA tool allowing biologists and biochemists to use the tool iwhtout having to directly change the code. 
The IPA tool uses MS1 and MS2 data for a bayesian annotation of small molecules. It does this by integrating isotope pattern detection, clustering, MSMS spectrum matching and optionally posterior inference using Gibbs sampler.

### The GUI supports:
- Positive/Negative ionisation modes
- Optional advanced control of the clustering and annotation parameters
- Flexible Export of results into csv, TSV or XLSX for increased user friendliness

## Installation

### App Installation

The easiest way to install the tool is via the link https://github.com/Callumf55/IPA_gui_app/releases/download/v0.1.6/IPA-Pipeline-GUI-Windows.zip This downloads all the relevent code and dependencies in one zip file with an application that opens the gui allowing for users to run the interface without having to interact with the code.

### Code installation
If the user wants to install the code and not the application then the following steps show how. However if the app is installed the following steps are not required.

First the IPA tool and it's dependencies should be installed accoring to https://github.com/francescodc87/ipaPy2/blob/main/README.ipynb

### 1. Clone the repository
```bash
git clone https://github.com/Callumf55/IPA_GUI.git
cd IPA_GUI
```

### 2. Create a virtual environment (Optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the App
```bash
python ipa_gui_advanced.py
```

## Required Inputs

| Input                  | Description                                              | Required |
|------------------------|----------------------------------------------------------|----------|
| MS1 Input File         | Feature table with m/z, RT, and intensity                | Yes      |
| Adducts File           | List of adducts used in annotation                       | Yes      |
| MS1 Database File      | Chemical formula + mass database (e.g. from HMDB)        | Yes      |
| MS2 Input File         | MS/MS spectral information                               | No       |
| MS2 Database File      | Required if MS2 data is included                         | No       |
| Biological Network File| Optional biochemical graph (for biochemical mode)        | No       |
| Output Directory       | Folder for saving all outputs                            | Yes      |

## Basic Settings (These are required to run the IPA tool)

| Setting              | Description                                                        |
|----------------------|--------------------------------------------------------------------|
| PPM                  | Maximum allowed mass deviation for candidate matching ([?](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppm)) |
| Ionisation Mode      | Choose between Positive or Negative ionisation                     |
| Gibbs Iterations     | Number of sampling steps for the Gibbs sampler ([?](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#gibbs-sampler-iterations)) |
| Gibbs Sampler Type   | Options: adduct, biochemical, or both                              |

## Advanced Settings

You can enable the advanced controls via the "Enable Advanced Settings" checkbox.

### Grouped settings (with full descriptions):

#### Clustering
- [Clustering Cthr](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-cthr)
- [Clustering RTwin](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-rtwin)
- [Clustering Intmode](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#clustering-intmode)

#### Isotope Detection
- [Isotope Mass Diff](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#isotope-mass-diff)
- [Min Isotope Ratio](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#min-isotope-ratio)
- [Isotope ppm](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#isotope-ppm)

#### Annotation
- [Electron Mass (me)](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#electron-mass-me)
- [Intensity Ratio SD](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#intensity-ratio-sd)
- [ppmunk](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmunk)
- [ratiounk](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ratiounk)
- [ppmthr](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmthr)
- [pRTNone](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#prtnone)
- [pRTout](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#prtout)

#### MSMS Settings
- [mzdCS](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#mzdcs)
- [ppmCS](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#ppmcs)
- [CSunk](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#csunk)
- evfilt: Enable evidence filtering

#### Gibbs Sampler Parameters
- [Burn-in Iterations](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#burn-in-iterations)
- [Delta (Adduct)](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#delta-adduct)
- [Delta (Bio)](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#delta-bio)
- [All Out](https://github.com/Callumf55/IPA_GUI/blob/main/README.md#all-out)

## Outputs

| File                         | Description                                   |
|------------------------------|-----------------------------------------------|
| summary_annotations.csv      | All annotations with probabilities            |
| most_likely_annotations.csv  | Filtered annotations (most probable per peak) |
| Intermediate logs or clusters| Saved in the output directory                 |

You can select export format as CSV, TSV, or XLSX.

## Developer Notes

- Main GUI file: `ipa_gui_advanced.py`
- Pipeline logic: `ipa_run_pipeline_ad.py`
- Annotation core: `ipa.py`
- To add parameters to the GUI, update `init_ui()` and `run_pipeline()`


