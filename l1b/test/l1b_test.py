
#FIRST CROSS VALIDATE L1B OUTPUTS EQUALIZED WITH TEACHER RESULTS
#PLOT FROM YOUR OUTPUTS THE EQUALISED OUPUT VERSUS NOT EQUALISED VERSUS THE TRUTH (LIKE FIGURE 8.3)
#TRUTH = EODP-TS-L1B\input\ism_toa_isrf_VNIR-0.nc
#THIRD EXPLAIN WHAT DO WE SEE IN THE PLOT (TO THE REPORT)
import os
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt

# =========================================================================
# Directory Configurations
# =========================================================================
dir_equalized = r"C:\Users\alexe\Downloads\EODP\EODP_TER_2021\EODP-TS-L1B\output_AEC_equalized"
dir_no_equalized = r"C:\Users\alexe\Downloads\EODP\EODP_TER_2021\EODP-TS-L1B\output_AEC_no_equalized"
dir_truth = r"C:\Users\alexe\Downloads\EODP\EODP_TER_2021\EODP-TS-L1B\input"

bands = [0, 1, 2, 3]

dir_teacher = r"C:\Users\alexe\Downloads\EODP\EODP_TER_2021\EODP-TS-L1B\output"


# =========================================================================
# Helper Function for File Comparison
# =========================================================================
def compare_folder_files(folder_path, folder_label):
    print("\n" + "=" * 75)
    print(f" CROSS-VALIDATION: {folder_label} vs. TEACHER OUTPUTS")
    print("=" * 75)

    if not os.path.exists(folder_path):
        print(f"⚠️ Folder not found: {folder_path}")
        return

    nc_files = [f for f in os.listdir(folder_path) if f.endswith('.nc')]

    if not nc_files:
        print(f"No .nc files found in {folder_path}")
        return

    for file_name in sorted(nc_files):
        file_user = os.path.join(folder_path, file_name)
        file_teacher = os.path.join(dir_teacher, file_name)

        if os.path.exists(file_teacher):
            ds_user = nc.Dataset(file_user)
            ds_teacher = nc.Dataset(file_teacher)

            var_user = list(ds_user.variables.keys())[-1]
            var_teacher = list(ds_teacher.variables.keys())[-1]

            data_user = ds_user.variables[var_user][:]
            data_teacher = ds_teacher.variables[var_teacher][:]

            mae = np.mean(np.abs(data_user - data_teacher))
            rmse = np.sqrt(np.mean((data_user - data_teacher) ** 2))
            max_diff = np.max(np.abs(data_user - data_teacher))

            status = "MATCH" if rmse < 1e-5 else "MISMATCH"
            print(f"[{status}] {file_name}:")
            print(f"    MAE: {mae:.6e} | RMSE: {rmse:.6e} | Max Diff: {max_diff:.6e}")

            ds_user.close()
            ds_teacher.close()
        else:
            print(f"[MISSING IN TEACHER DIR] {file_name}")


# =========================================================================
# STEP 1: Compare ALL files in BOTH user directories against teacher outputs
# =========================================================================
compare_folder_files(dir_equalized, "EQUALIZED FOLDER (output_AEC_equalized)")
compare_folder_files(dir_no_equalized, "NO EQUALIZED FOLDER (output_AEC_no_equalized)")
print("=" * 75 + "\n")

# Create figure with 4 vertically stacked subplots
fig, axes = plt.subplots(4, 1, figsize=(9, 12))

for idx, band in enumerate(bands):
    # File path constructions
    file_eq = os.path.join(dir_equalized, f"l1b_toa_VNIR-{band}.nc")
    file_no_eq = os.path.join(dir_no_equalized, f"l1b_toa_VNIR-{band}.nc")
    file_truth = os.path.join(dir_truth, f"ism_toa_isrf_VNIR-{band}.nc")

    # Fallback naming checks for output files
    if not os.path.exists(file_eq):
        file_eq = os.path.join(dir_equalized, f"l1b_toa_eq_VNIR-{band}.nc")
    if not os.path.exists(file_no_eq):
        file_no_eq = os.path.join(dir_no_equalized, f"l1b_toa_eq_VNIR-{band}.nc")

    if not (os.path.exists(file_eq) and os.path.exists(file_no_eq) and os.path.exists(file_truth)):
        print(f"⚠️ Missing required file(s) for Band VNIR-{band}:")
        if not os.path.exists(file_truth):
            print(f"   - Truth file missing: {file_truth}")
        continue

    # Load NetCDF datasets
    ds_eq = nc.Dataset(file_eq)
    ds_no_eq = nc.Dataset(file_no_eq)
    ds_truth = nc.Dataset(file_truth)

    # Extract data matrices
    data_eq = ds_eq.variables[list(ds_eq.variables.keys())[-1]][:]
    data_no_eq = ds_no_eq.variables[list(ds_no_eq.variables.keys())[-1]][:]
    data_truth = ds_truth.variables[list(ds_truth.variables.keys())[-1]][:]

    # Extract line 0 (toa_truth[i][0])
    line_eq = data_eq[0] if data_eq.ndim >= 2 else data_eq
    line_no_eq = data_no_eq[0] if data_no_eq.ndim >= 2 else data_no_eq
    line_truth = data_truth[0] if data_truth.ndim >= 2 else data_truth

    # Plot on corresponding subplot
    ax = axes[idx]
    ax.plot(line_truth, label="Truth", color="#1f77b4", linewidth=1.5)        # Blue
    ax.plot(line_eq, label="Equalizer", color="#ff7f0e", linewidth=1.2)       # Orange
    ax.plot(line_no_eq, label="Not Equalizer", color="#2ca02c", linewidth=1.2) # Green

    ax.set_title(f"VNIR-{band}", fontsize=11, fontweight="bold")
    ax.set_xlabel("Sample", fontsize=9)
    ax.set_ylabel("TOA", fontsize=9)
    ax.grid(True, linestyle="-", linewidth=0.5, alpha=0.7)
    ax.legend(loc="upper left", fontsize=8)

    # Close NetCDF files
    ds_eq.close()
    ds_no_eq.close()
    ds_truth.close()

plt.tight_layout()
plt.show()