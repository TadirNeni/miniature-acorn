import pandas as pd

# Load the newly merged dataset
df = pd.read_parquet('datasets/cicids2017.parquet')

# Print the columns in a clean list format
print("--- OFFICIAL FEATURE LIST ---")
features = list(df.columns)
for i, col in enumerate(features):
    print(f"{i}: {col}")

print(f"\nTOTAL COLUMNS: {len(features)}")