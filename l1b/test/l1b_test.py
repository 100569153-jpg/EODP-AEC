
#FIRST CROSS VALIDATE L1B OUTPUTS EQUALIZED WITH TEACHER RESULTS
#PLOT FROM YOUR OUTPUTS THE EQUALISED OUPUT VERSUS NOT EQUALISED VERSUS THE TRUTH (LIKE FIGURE 8.3)
#TRUTH = EODP-TS-L1B\input\ism_toa_isrf_VNIR-0.nc
#THIRD EXPLAIN WHAT DO WE SEE IN THE PLOT (TO THE REPORT)
import os
import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt

import os
import numpy as np
import matplotlib.pyplot as plt
from common.io.writeToa import readToa
# =========================================================================
# Directory Configurations
# =========================================================================
dir_eq = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/output_AEC_equalized"
dir_no_eq = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/output_AEC_no_equalized"
dir_ref = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/output"
dir_isrf = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/input"
dir_fig = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/figures_AEC"
bands = ['VNIR-0', 'VNIR-1', 'VNIR-2', 'VNIR-3']
threshold = 1e-3  # [%] maximum relative difference allowed (guide to the subject)

if not os.path.isdir(dir_fig):
    os.makedirs(dir_fig)
# =========================================================================
# Cross validation with the reference outputs (teacher ones)
# =========================================================================
results = []
for band in bands:
    for name in ['l1b_toa_eq_', 'l1b_toa_']:
        toa_mine = readToa(dir_eq, name + band + '.nc')
        toa_ref = readToa(dir_ref, name + band + '.nc')

        # Relative difference in % (avoid dividing by zero)
        diff = np.abs(toa_mine - toa_ref)
        rel_diff = np.zeros(diff.shape)
        mask = toa_ref != 0
        rel_diff[mask] = diff[mask] / np.abs(toa_ref[mask]) * 100

        # Points below the threshold, and the 3-sigma value of the relative difference
        perc_ok = np.sum(rel_diff < threshold) / rel_diff.size * 100
        rel_3sigma = np.mean(rel_diff) + 3 * np.std(rel_diff)
        result = 'PASS' if np.max(rel_diff) < threshold else 'FAIL'

        line = (name + band + ': max abs diff = ' + '%.3e' % np.max(diff) +
                ', max rel diff = ' + '%.3e' % np.max(rel_diff) + ' %' +
                ', 3-sigma rel diff = ' + '%.3e' % rel_3sigma + ' %' +
                ', points < ' + str(threshold) + '% = ' + '%.2f' % perc_ok + ' %  -> ' + result)
        print(line)
        results.append(line)

with open(os.path.join(dir_fig, 'l1b_crossvalidation.txt'), 'w') as f:
    f.write('\n'.join(results))

# =========================================================================
# Plot equalized vs not equalizaed vs TOA after the ISRF (Central ALT lien)
# =========================================================================

for band in bands:
    toa_eq = readToa(dir_eq, 'l1b_toa_' + band + '.nc')
    toa_no_eq = readToa(dir_no_eq, 'l1b_toa_' + band + '.nc')
    toa_isrf = readToa(dir_isrf, 'ism_toa_isrf_' + band + '.nc')

    idalt = int(toa_eq.shape[0] / 2)

    fig = plt.figure(figsize=(10, 7))
    plt.plot(toa_isrf[idalt, :], '-b', label='TOA after the ISRF')
    plt.plot(toa_no_eq[idalt, :], '-g', label='L1B TOA without equalization')
    plt.plot(toa_eq[idalt, :], '-r', label='L1B TOA with equalization')
    plt.title('Effect of the equalization for ' + band + ' (ALT line ' + str(idalt) + ')', fontsize=16)
    plt.xlabel('ACT pixel [-]', fontsize=14)
    plt.ylabel('TOA [mW/m2/sr]', fontsize=14)
    plt.legend()
    plt.grid()
    saveas = os.path.join(dir_fig, 'l1b_equalization_' + band + '.png')
    plt.savefig(saveas)
    plt.close(fig)
    print('Saved image ' + saveas)
