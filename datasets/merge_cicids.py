import pandas as pd
import os

# Configuration
data_folder = 'datasets/'
output_file = 'datasets/cicsid2017.parquet'
samples_per_file = 40000  # 40k x 5 files = 200k rows (Solid for B.Sc. scale)

all_dfs = []

# Full list of subsets for a comprehensive IDS
files = [
    'Botnet-Friday-no-metadata.parquet',
    'Infiltration-Thursday-no-metadata.parquet',
    'DDoS-Friday-no-metadata.parquet',
    'Portscan-Friday-no-metadata.parquet',
    'WebAttacks-Thursday-no-metadata.parquet' # Newly added
]

print("🚀 Initializing Expanded CIC-IDS2017 Fusion...")

for file in files:
    path = os.path.join(data_folder, file)
    if os.path.exists(path):
        print(f"-> Processing {file}...")
        df = pd.read_parquet(path)
        
        # Downsampling for balance
        if len(df) > samples_per_file:
            df = df.sample(n=samples_per_file, random_state=42)
        
        all_dfs.append(df)
    else:
        print(f"![Warning] {file} not found. Ensure it is in the 'datasets/' folder.")

if all_dfs:
    master_df = pd.concat(all_dfs, axis=0, ignore_index=True)
    
    # Standardize column naming
    master_df.columns = master_df.columns.str.strip()
    
    # Final export
    master_df.to_parquet(output_file)
    
    print(f"\n✅ SUCCESS: Unified dataset created at {output_file}")
    print(f"Total Rows: {len(master_df)}")
    
    target_col = master_df.columns[-1]
    print(f"Detected Attack Classes:\n{master_df[target_col].value_counts()}")
else:
    print("\n❌ ERROR: No files found.")