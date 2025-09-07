import os
import pandas as pd
from ipa import simpleIPA, clusterFeatures, map_isotope_patterns, compute_all_adducts, Gibbs_sampler_add, MSMSannotation, MS1annotation, Gibbs_sampler_bio, Gibbs_sampler_bio_add

def run_ipa_pipeline(
    ms1_input_path,
    adducts_path,
    db_ms1_path,
    output_dir,
    ms2_input_path=None,  
    db_ms2_path=None,     
    ionisation=None,
    ppm=10,
    run_clustering=True,
    run_gibbs=False,
    gibbs_iterations=1000,
    gibbs_version="adduct",
    Bio=None,
    export_format="csv",
    summary_filename="summary.csv",
    most_likely_filename=None,
    ncores=1,
    # Advanced options
    advanced_options=None
):
    # Required inputs (MS1 + adducts + MS1 DB)
    if not os.path.exists(ms1_input_path):
        raise FileNotFoundError(f"MS1 input file not found: {ms1_input_path}")
    if not os.path.exists(adducts_path):
        raise FileNotFoundError(f"Adducts file not found: {adducts_path}")
    if not os.path.exists(db_ms1_path):
        raise FileNotFoundError(f"MS1 database file not found: {db_ms1_path}")

    # Parameter validations
    if ionisation is None:
        raise ValueError("Parameter 'ionisation' is required (e.g., 'Positive' or 'Negative').")

    # Optional MS2 inputs (only validate if BOTH provided)
    if ms2_input_path and db_ms2_path:
        if not os.path.exists(ms2_input_path):
            raise FileNotFoundError(f"MS2 input file not found: {ms2_input_path}")
        if not os.path.exists(db_ms2_path):
            raise FileNotFoundError(f"MS2 database file not found: {db_ms2_path}")
    else:
        if ms2_input_path or db_ms2_path:
            print("MS2 inputs incomplete, running MS1-only.")
        # If one or both are missing, force MS1-only path
        ms2_input_path, db_ms2_path = None, None

    os.makedirs(output_dir, exist_ok=True)

    print("Step 1: Loading MS1 input data...")
    df_raw = pd.read_csv(ms1_input_path)

    # Set defaults or override with advanced
    advanced = advanced_options or {}
    ncores_eff = advanced.get("ncores", ncores)
    ncores_eff = max(1, min(ncores_eff, os.cpu_count() or 1))

    if run_clustering:
        print("Step 2: Running clustering on MS1 features...")
        df = clusterFeatures(
            df_raw,
            Cthr=advanced.get("clustering_Cthr", 0.8),
            RTwin=advanced.get("clustering_RTwin", 1),
            Intmode=advanced.get("clustering_Intmode", "max")
        )
    else:
        print("Step 2: Clustering skipped.")
        df = df_raw

    print("Step 3: Mapping isotope patterns...")
    map_isotope_patterns(
        df,
        isoDiff=advanced.get("isoDiff", 1),
        ppm=advanced.get("isotope_ppm", 100),
        ionisation=ionisation,
        MinIsoRatio=advanced.get("MinIsoRatio", 0.5)
    )

    print("Step 4: Loading adducts and MS1 database...")
    adducts = pd.read_csv(adducts_path)
    db = pd.read_csv(db_ms1_path)

    print("Step 5: Computing all adduct formulas...")
    allAdds = compute_all_adducts(
        adducts,
        db,
        ionisation=ionisation,
        ncores=ncores_eff
    )

    if ms2_input_path and db_ms2_path:
        print("Step 6: Performing MS2-based annotation...")
        dfMS2 = pd.read_csv(ms2_input_path)
        DBMS2 = pd.read_csv(db_ms2_path)
        annotations = MSMSannotation(
            df, dfMS2, allAdds, DBMS2, ppm,
            me=advanced.get("me", 5.48579909065e-04),
            ratiosd=advanced.get("ratiosd", 0.9),
            ppmunk=advanced.get("ppmunk"),
            ratiounk=advanced.get("ratiounk"),
            ppmthr=advanced.get("ppmthr"),
            pRTNone=advanced.get("pRTNone"),
            pRTout=advanced.get("pRTout"),
            mzdCS=advanced.get("mzdCS", 0),
            ppmCS=advanced.get("ppmCS", 10),
            CSunk=advanced.get("CSunk", 0.7),
            evfilt=advanced.get("evfilt", False),
            ncores=ncores_eff
        )
    else:
        print("Step 6: Performing MS1-only annotation (no MS2 inputs provided or validated).")
        annotations = MS1annotation(
            df, allAdds, ppm,
            me=advanced.get("me", 5.48579909065e-04),
            ratiosd=advanced.get("ratiosd", 0.9),
            ppmunk=advanced.get("ppmunk"),
            ratiounk=advanced.get("ratiounk"),
            ppmthr=advanced.get("ppmthr"),
            pRTNone=advanced.get("pRTNone"),
            pRTout=advanced.get("pRTout"),
            ncores=ncores_eff
        )

    if run_gibbs:
        print(f"Step 7: Running Gibbs sampler ({gibbs_version})...")
        burn = advanced.get("burn", None)
        all_out = advanced.get("all_out", False)

        if gibbs_version == "adduct":
            Gibbs_sampler_add(
                df, annotations,
                noits=gibbs_iterations,
                burn=burn,
                delta_add=advanced.get("delta_add", 1),
                all_out=all_out
            )
        elif gibbs_version == "biochemical":
            if not Bio or not os.path.exists(Bio):
                raise FileNotFoundError("Biological network file is required for 'biochemical' Gibbs sampler.")
            bio_df = pd.read_csv(Bio)
            Gibbs_sampler_bio(
                df, annotations, Bio=bio_df,
                noits=gibbs_iterations,
                burn=burn,
                delta_bio=advanced.get("delta_bio", 1),
                all_out=all_out
            )
        elif gibbs_version == "biochemical and adduct":
            if not Bio or not os.path.exists(Bio):
                raise FileNotFoundError("Biological network file is required for 'biochemical and adduct' Gibbs sampler.")
            bio_df = pd.read_csv(Bio)
            Gibbs_sampler_bio_add(
                df, annotations, Bio=bio_df,
                noits=gibbs_iterations,
                burn=burn,
                delta_bio=advanced.get("delta_bio", 1),
                delta_add=advanced.get("delta_add", 1),
                all_out=all_out
            )
        else:
            raise ValueError(f"Unsupported Gibbs sampler version: {gibbs_version}")

    print("Step 8: Building merged output table...")
    out = []
    # Safe handling if annotations is empty
    if len(annotations) == 0:
        cols = []
    else:
        first_key = next(iter(annotations))
        cols = list(annotations[first_key].columns)

    for k in df.ids:
        tmp = df[df['ids'] == k].copy()
        if k in annotations:
            tmp2 = annotations[k].copy().reset_index(drop=True)
            tmp = tmp.loc[tmp.index.repeat(len(tmp2.index))].reset_index(drop=True)
            tmp = pd.concat([tmp, tmp2], axis=1)
        else:
            tmp2 = pd.DataFrame(columns=cols)
            tmp = pd.concat([tmp, tmp2], axis=1)
        out.append(tmp)

    res = pd.concat(out, axis=0, ignore_index=True)
    res.insert(0, '', range(1, len(res) + 1))

    print(f"Step 9: Exporting summary table as {export_format}...")
    summary_path = os.path.join(output_dir, summary_filename)
    export_summary_table(res, summary_path, export_format)

    if most_likely_filename:
        print(f"Step 10: Exporting most likely annotations as {export_format}...")
        selected_indices = []
        for k in df.ids:
            tmp = res[res['ids'] == k].copy()
            if tmp.empty:
                continue
            if 'post Gibbs' in tmp.columns and tmp['post Gibbs'].notna().any():
                best_idx = tmp['post Gibbs'].idxmax()
            elif 'post' in tmp.columns and tmp['post'].notna().any():
                best_idx = tmp['post'].idxmax()
            else:
                best_idx = tmp.index[0]
            selected_indices.append(best_idx)
        res_max_likely = res.loc[selected_indices].copy()
        most_likely_path = os.path.join(output_dir, most_likely_filename)
        export_summary_table(res_max_likely, most_likely_path, export_format)
    else:
        print("Step 10: Skipped exporting most likely annotations (disabled by user).")

    print("Pipeline completed successfully.")

def export_summary_table(res: pd.DataFrame, output_path: str, export_format: str):
    if export_format == "csv":
        res.to_csv(output_path, index=False)
    elif export_format == "tsv":
        res.to_csv(output_path, sep="\t", index=False)
    elif export_format == "xlsx":
        if not output_path.endswith(".xlsx"):
            output_path = os.path.splitext(output_path)[0] + ".xlsx"
        res.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")
