# E2E TEST
# Full chain ISM -> L1B -> L1C with the new scene and the new instrument configuration (last class)
# For each band: L1B TOA image with its histogram next to it

import os
import numpy as np
import matplotlib.pyplot as plt
from common.io.writeToa import readToa
from common.src.auxFunc import getIndexBand
from config.l1bConfig import l1bConfig
from config.ismConfig import ismConfig

# Directories
dir_ism = r"C:/Users/alexe/Downloads/EODP/EODP-TS-E2E/output_AEC_2"
dir_l1b = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/output_AEC_last class"
dir_fig = r"C:/Users/alexe/Downloads/EODP/EODP-TS-E2E/figures_AEC"

bands = ['VNIR-0', 'VNIR-1', 'VNIR-2', 'VNIR-3']

if not os.path.isdir(dir_fig):
    os.makedirs(dir_fig)

gain = l1bConfig().gain
max_dn = 2 ** ismConfig().bit_depth - 1

# -------------------------------------------------------------------------------
# 1. L1B TOA image and histogram for each band
# -------------------------------------------------------------------------------
lines = []
for band in bands:
    toa_l1b = readToa(dir_l1b, 'l1b_toa_' + band + '.nc')
    toa_dn = readToa(dir_ism, 'ism_toa_' + band + '.nc')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    im = ax1.imshow(toa_l1b, cmap='jet', aspect='auto')
    fig.colorbar(im, ax=ax1, label='TOA [mW/m2/sr]')
    ax1.set_title('L1B TOA ' + band, fontsize=14)
    ax1.set_xlabel('ACT pixel [-]')
    ax1.set_ylabel('ALT pixel [-]')

    ax2.hist(toa_l1b.flatten(), bins=100, color='b')
    ax2.set_title('Histogram of the L1B TOA ' + band, fontsize=14)
    ax2.set_xlabel('TOA [mW/m2/sr]')
    ax2.set_ylabel('Number of pixels')
    ax2.grid()

    plt.tight_layout()
    saveas = os.path.join(dir_fig, 'e2e_l1b_toa_hist_' + band + '.png')
    plt.savefig(saveas)
    plt.close(fig)
    print('Saved image ' + saveas)

    # Statistics of the band
    n_sat = np.sum(toa_dn >= max_dn)
    lines.append(band + ': L1B TOA min = %.2f, max = %.2f, mean = %.2f, std = %.2f mW/m2/sr'
                 % (np.min(toa_l1b), np.max(toa_l1b), np.mean(toa_l1b), np.std(toa_l1b)) +
                 ' | saturated pixels = ' + str(n_sat) + ' of ' + str(toa_l1b.size) +
                 ' | saturation radiance = %.2f mW/m2/sr' % (max_dn * gain[getIndexBand(band)]))

for line in lines:
    print(line)
with open(os.path.join(dir_fig, 'e2e_statistics.txt'), 'w') as f:
    f.write('\n'.join(lines))