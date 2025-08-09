import os
import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QPushButton,
    QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QTextEdit, QDoubleSpinBox, QGroupBox, QSizePolicy, QSpinBox
)
from ipa import simpleIPA, clusterFeatures, map_isotope_patterns, compute_all_adducts, Gibbs_sampler_add, MSMSannotation, MS1annotation, Gibbs_sampler_bio, Gibbs_sampler_bio_add

def run_ipa_pipeline(
    ms1_input_path,
    adducts_path,
    db_ms1_path,
    output_dir,
    ms2_input_path,
    db_ms2_path,
    ionisation,
    ppm,
    run_clustering,
    run_gibbs,
    gibbs_iterations,
    gibbs_version,
    Bio,
    export_format,
    summary_filename
):
    if not os.path.exists(ms1_input_path):
        raise FileNotFoundError(f"MS1 input file not found: {ms1_input_path}")
    if not os.path.exists(adducts_path):
        raise FileNotFoundError(f"Adducts file not found: {adducts_path}")
    if not os.path.exists(db_ms1_path):
        raise FileNotFoundError(f"MS1 database file not found: {db_ms1_path}")
    if ms2_input_path and not os.path.exists(ms2_input_path):
        raise FileNotFoundError(f"MS2 input file not found: {ms2_input_path}")
    if db_ms2_path and not os.path.exists(db_ms2_path):
        raise FileNotFoundError(f"MS2 database file not found: {db_ms2_path}")

    os.makedirs(output_dir, exist_ok=True)

    print("Step 1: Loading MS1 input data...")
    df_raw = pd.read_csv(ms1_input_path)

    if run_clustering:
        print("Step 2: Running clustering on MS1 features...")
        df = clusterFeatures(df_raw)
    else:
        print("Step 2: Clustering skipped.")
        df = df_raw

    print("Step 3: Mapping isotope patterns...")
    map_isotope_patterns(df, ionisation=ionisation)

    print("Step 4: Loading adducts and MS1 database...")
    adducts = pd.read_csv(adducts_path)
    db = pd.read_csv(db_ms1_path)

    print("Step 5: Computing all adduct formulas...")
    allAdds = compute_all_adducts(adducts, db, ionisation)

    if ms2_input_path and db_ms2_path:
        print("Step 6: Performing MS2-based annotation...")
        dfMS2 = pd.read_csv(ms2_input_path)
        DBMS2 = pd.read_csv(db_ms2_path)
        annotations = MSMSannotation(df, dfMS2, allAdds, DBMS2, ppm)
    else:
        print("Step 6: Performing MS1-only annotation...")
        annotations = MS1annotation(df, allAdds, ppm)

    if run_gibbs:
        print(f"Step 7: Running Gibbs sampler ({gibbs_version})...")
        if gibbs_version == "adduct":
            from ipa import Gibbs_sampler_add as sampler
            sampler_kwargs = {}
        elif gibbs_version == "biochemical":
            from ipa import Gibbs_sampler_bio as sampler
            if not Bio or not os.path.exists(Bio):
                raise FileNotFoundError("Biological network file is required for 'biochemical' Gibbs sampler.")
            bio_df = pd.read_csv(Bio)
            sampler_kwargs = {"Bio": bio_df}
        elif gibbs_version == "biochemical and adduct":
            from ipa import Gibbs_sampler_bio_add as sampler
            if not Bio or not os.path.exists(Bio):
                raise FileNotFoundError("Biological network file is required for 'biochemical and adduct' Gibbs sampler.")
            bio_df = pd.read_csv(Bio)
            sampler_kwargs = {"Bio": bio_df}
        else:
            raise ValueError(f"Unsupported Gibbs sampler version: {gibbs_version}")

        sampler(df, annotations, noits=gibbs_iterations, **sampler_kwargs)

        print("Step 8: Exporting summary table...")
        summary_path = os.path.join(output_dir, summary_filename)
        export_summary_table(annotations, summary_path)

    print("Step 9: Exporting individual annotations...")
    export_annotations(annotations, output_dir, export_format)

    print("Pipeline completed successfully.")
    return annotations

def export_annotations(annotations: dict, output_dir: str, format='csv'):
    for feature_id, df_ann in annotations.items():
        out_path = os.path.join(output_dir, f"annotation_{feature_id}.{format}")
        df_ann.to_csv(out_path, index=False)

def export_summary_table(annotations: dict, output_path: str):
    all_rows = []
    for feature_id, df_ann in annotations.items():
        df_ann = df_ann.copy()
        df_ann['feature_id'] = feature_id
        all_rows.append(df_ann)
    summary_df = pd.concat(all_rows)
    summary_df.to_csv(output_path, index=False)
