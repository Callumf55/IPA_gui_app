import pandas as pd
import re

# Load the LAMP clustered annotations and the raw dataset
anno_df = pd.read_csv("C:/Users/callu/LAMP/anno_summ_IPA.csv")
raw_df = pd.read_csv("C:/Users/callu/LAMP/lamp/examples/data/df_test_pos_not_clustered.csv")

# Step 1: Filter only annotated rows with valid compound name and cor_grp
annotated_df = anno_df[anno_df['compound_name'].notna() & anno_df['cor_grp'].notna()].copy()

# Step 2: Split cor_grp and ion_type into lists
# Step 2: Split ids, adducts, and compound names into lists
annotated_df['cor_grp'] = annotated_df['cor_grp'].astype(str)
annotated_df['ids'] = annotated_df['cor_grp'].str.split('::')
annotated_df['adducts'] = annotated_df['ion_type'].str.split('::')
annotated_df['compound_names'] = annotated_df['compound_name'].str.split('::')
annotated_df['formulas'] = annotated_df['molecular_formula'].str.split('::')
# Step 3: Expand one row per id with corresponding adduct and compound name
expanded_rows = []
for _, row in annotated_df.iterrows():
    ids = row['ids']
    adducts = row['adducts'] if isinstance(row['adducts'], list) else [None] * len(ids)
    names = row['compound_names'] if isinstance(row['compound_names'], list) else [None] * len(ids)
    formulas = row['formulas'] if isinstance(row['formulas'], list) else [None] * len(ids)
    for i, id_val in enumerate(ids):
        expanded_rows.append({
            'cor_grp': row['cor_grp'],
            'ids': int(id_val),
            'ion_type': row['ion_type'],
            'adduct': adducts[i] if i < len(adducts) else None,
            'compound_name': names[i] if i < len(names) else None,
            'formula' : formulas[i] if i < len(formulas) else None
        })

annotated_exploded = pd.DataFrame(expanded_rows)


# Step 4: Assign relative_id per cor_grp
annotated_exploded['relative_id'] = annotated_exploded.groupby('cor_grp').ngroup()

# Step 5: Compute mean intensity across sample columns
sample_cols = [col for col in raw_df.columns if col.startswith("sample")]
raw_df['intensity'] = raw_df[sample_cols].mean(axis=1)

# Step 6: Merge mz, rt, and intensity from raw_df
merged_df = pd.merge(
    annotated_exploded,
    raw_df[['ids', 'mzs', 'RTs', 'intensity']],
    on='ids',
    how='left'
)

# Step 7: Default all to 'potential bp'
merged_df['relationship'] = 'potential bp'

# Step 8: Mark any row with '13C' in the adduct as 'bp|isotope'
merged_df.loc[merged_df['adduct'].str.contains('13C', case=False, na=False), 'relationship'] = 'bp|isotope'

# Step 9: For each group, assign 'bp' to the highest intensity IF not already labeled as 'bp|isotope'
idx_max_intensity = merged_df.groupby('cor_grp')['intensity'].idxmax()
for idx in idx_max_intensity:
    if merged_df.loc[idx, 'relationship'] != 'bp|isotope':
        merged_df.loc[idx, 'relationship'] = 'bp'

# Step 10: Extract charge from ion_type
def extract_charge(ion_type):
    if isinstance(ion_type, str):
        matches = re.findall(r'\[.*?\][+-]?\d*', ion_type)
        if matches:
            ion = matches[-1]
            match = re.search(r'(\d*)([+-])$', ion)
            if match:
                number = match.group(1)
                sign = match.group(2)
                return int(number or '1') * (1 if sign == '+' else -1)
    return 0

merged_df['charge'] = merged_df['ion_type'].apply(extract_charge)

# Step 11: Assign feature_id
merged_df['feature_id'] = [str(i + 1) for i in range(len(merged_df))]

# Step 12: Build final IPA-compatible DataFrame
ipa_df = merged_df[['feature_id', 'ids', 'relative_id', 'mzs', 'RTs',
                    'intensity', 'relationship', 'charge', 'adduct', 'compound_name', 'formula']]
ipa_df = ipa_df.rename(columns={'mzs': 'mz', 'RTs': 'rt'})

# Step 13: Save to file
ipa_df.to_csv("C:/Users/callu/LAMP/annotated_IPA_df.csv", index=False)
print("Saved: annotated_IPA_df.csv")
