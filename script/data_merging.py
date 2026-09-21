import glob
import os
import pandas as pd
from pathlib import Path

# 1. Define WSL/Linux directory paths
base_dir = Path("/mnt/c/Users/wei.kc/Desktop/Adhoc/03 Sept 2026/data/VN_order(July-Aug)")
july_dir = base_dir / "July2026"
aug_dir = base_dir / "Aug2026"

output_dir = base_dir / "Compiled_Output"
test_out_dir = base_dir / "Test_Verification_Output"

output_dir.mkdir(parents=True, exist_ok=True)
test_out_dir.mkdir(parents=True, exist_ok=True)

# 2. String ID columns
STRING_ID_COLS = [
    "order_display_id",
    "user_id",
    "driver_id",
    "user_name",
    "order_remark",
    "start_address",
    "end_address",
]

def load_and_clean_chunk(file_path):
    """Reads CSV or Excel chunk, forcing ID columns to str."""
    ext = Path(file_path).suffix.lower()
    dtype_map = {col: str for col in STRING_ID_COLS}

    try:
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, dtype=dtype_map)
        elif ext == ".csv":
            df = pd.read_csv(file_path, dtype=dtype_map)
        else:
            return None
    except Exception as e:
        print(f"  [ERROR] Failed to read {os.path.basename(file_path)}: {e}")
        return None

    # Clean trailing '.0' artifacts
    for col in STRING_ID_COLS:
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            )
            df[col] = df[col].replace(["nan", "NaN", "NULL", "None", ""], None)

    return df

def compile_monthly_chunks(
    month_folder,
    month_name,
    out_directory,
    max_files=None,
    force_recompile=True,  # SET TO TRUE to force Parquet creation even if CSV exists
):
    file_tag = f"{month_name}_sample_{max_files}files" if max_files else month_name
    csv_output = out_directory / f"VN_order_compiled_{file_tag}.csv"
    parquet_output = out_directory / f"VN_order_compiled_{file_tag}.parquet"

    # Only skip if BOTH CSV and Parquet files exist
    if not force_recompile and csv_output.exists() and parquet_output.exists():
        print(f"\n[SKIP] Both CSV and Parquet files already exist for '{month_name}'. Skipping.")
        return

    print(f"\n==================================================")
    print(f"Processing {month_name} ({'Sample Mode: First ' + str(max_files) + ' files' if max_files else 'Full Mode'})")
    print(f"Folder: '{month_folder}'")
    print(f"==================================================")

    file_patterns = ["*.xlsx", "*.xls", "*.csv"]
    chunk_files = []
    for pattern in file_patterns:
        chunk_files.extend(glob.glob(os.path.join(month_folder, pattern)))

    if not chunk_files:
        print(f"[WARNING] No order chunk files found in '{month_folder}'!")
        return

    chunk_files = sorted(chunk_files)
    if max_files:
        chunk_files = chunk_files[:max_files]

    print(f"Found {len(chunk_files)} file chunk(s) to process. Compiling...")

    dataframes = []
    for file in chunk_files:
        print(f"  --> Reading: {os.path.basename(file)}")
        df_chunk = load_and_clean_chunk(file)
        if df_chunk is not None and not df_chunk.empty:
            dataframes.append(df_chunk)

    if not dataframes:
        print(f"[WARNING] No valid data extracted for {month_name}.")
        return

    combined_df = pd.concat(dataframes, ignore_index=True)

    # Deduplicate exact duplicate orders
    initial_cnt = len(combined_df)
    if "order_display_id" in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=["order_display_id"])
        print(f"--> Deduplicated orders: {initial_cnt:,} --> {len(combined_df):,} rows.")

    # Chronological sort
    if "order_creation_local_time" in combined_df.columns:
        combined_df["order_creation_local_time"] = pd.to_datetime(
            combined_df["order_creation_local_time"]
        )
        combined_df = combined_df.sort_values(by=["user_id", "order_creation_local_time"])

    # Explicitly force string ID columns to object type before Parquet write
    for col in STRING_ID_COLS:
        if col in combined_df.columns:
            combined_df[col] = combined_df[col].astype(str)

    # Output 1: Safe CSV Output
    combined_df.to_csv(csv_output, index=False, quoting=1)
    print(f"  [SUCCESS] Saved CSV: {csv_output} ({len(combined_df):,} rows)")

    # Output 2: Parquet Output
    try:
        combined_df.to_parquet(parquet_output, index=False, engine='pyarrow')
        print(f"  [SUCCESS] Saved Parquet: {parquet_output}")
    except Exception as e:
        print(f"  [ERROR] Parquet export failed for {month_name}: {e}")


# ==============================================================================
# RUN FULL COMPILATION (All files of July & August)
# ==============================================================================
print("\n>>> RUNNING FULL COMPILATION FOR JULY & AUGUST <<<")
compile_monthly_chunks(july_dir, "July2026", output_dir, max_files=None, force_recompile=True)
compile_monthly_chunks(aug_dir, "Aug2026", output_dir, max_files=None, force_recompile=True)

print("\nProcessing complete! Both July and August Parquet files are generated.")