#ISM UNITARY TEST
# 1. Cross validation of ALL my ISM outputs (isrf, optical, MTFs, detection, vcu, final DN) with the teacher outputs
# 2. Unit conversion: factors from radiance to DN and the value of the pixel [50,75] for the 4 bands,
#    compared with my outputs
# 3. System MTF and its 6 contributors (ACT and ALT cuts) and which one is the defining MTF of the system

import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from config.ismConfig import ismConfig
from auxiliary.constants import constants

# Directories
dir_mine = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-ISM/output_AEC_2"
dir_ref = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-ISM/output"
dir_fig = r"C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-ISM/figures_AEC"

bands = ['VNIR-0', 'VNIR-1', 'VNIR-2', 'VNIR-3']
threshold = 1e-3  # [%] maximum relative difference allowed (guide to the subject)

if not os.path.isdir(dir_fig):
    os.makedirs(dir_fig)


def readNc(directory, filename):
    # The TOA files have the variable 'toa' and the MTF files the variable 'mat'
    dset = Dataset(os.path.join(directory, filename))
    name = 'toa' if 'toa' in dset.variables else 'mat'
    data = np.array(dset.variables[name][:])
    dset.close()
    return data


# -------------------------------------------------------------------------------
# 1. Cross validation with the reference outputs (all the .nc files of the teacher)
# -------------------------------------------------------------------------------
results = []
for file in sorted(os.listdir(dir_ref)):
    if not file.endswith('.nc'):
        continue
    if not os.path.isfile(os.path.join(dir_mine, file)):
        line = file + ': NOT FOUND in my outputs'
        print(line)
        results.append(line)
        continue

    mine = readNc(dir_mine, file)
    ref = readNc(dir_ref, file)

    diff = np.abs(mine - ref)
    rel_diff = np.zeros(diff.shape)
    mask = ref != 0
    rel_diff[mask] = diff[mask] / np.abs(ref[mask]) * 100

    perc_ok = np.sum(rel_diff < threshold) / rel_diff.size * 100
    result = 'PASS' if np.max(rel_diff) < threshold else 'FAIL'

    line = (file + ': max abs diff = ' + '%.3e' % np.max(diff) +
            ', max rel diff = ' + '%.3e' % np.max(rel_diff) + ' %' +
            ', points < ' + str(threshold) + '% = ' + '%.2f' % perc_ok + ' %  -> ' + result)
    print(line)
    results.append(line)

with open(os.path.join(dir_fig, 'ism_crossvalidation.txt'), 'w') as f:
    f.write('\n'.join(results))

# -------------------------------------------------------------------------------
# 2. Unit conversion for the pixel [50,75]
# -------------------------------------------------------------------------------
cfg = ismConfig()
cte = constants()
ialt, iact = 50, 75

# Factors that do not depend on the band
X = np.pi / 4 * (cfg.D / cfg.f) ** 2 * cfg.Tr  # radiance -> irradiance [mW/m2 / (mW/m2/sr)]
e2V = cfg.OCF * cfg.ADC_gain  # electrons -> volts [V/e-]
V2DN = (2 ** cfg.bit_depth - 1) / (cfg.max_voltage - cfg.min_voltage)  # volts -> DN [DN/V]

lines = []
lines.append('Factors: X = %.6e, QE = %.2f e-/ph, e2V = %.6e V/e-, V2DN = %.4f DN/V' % (X, cfg.QE, e2V, V2DN))
lines.append('band | Y [ph/(mW/m2)] | L [mW/m2/sr] | I [mW/m2] | ph | e- | V | DN (theory) || '
             'I mine | e- mine | DN mine')

for band in bands:
    ib = int(band[-1])
    e_photon = cte.h_planck * cte.speed_light / cfg.wv[ib]
    Y = cfg.pix_size ** 2 * cfg.t_int / e_photon / 1000  # irradiance -> photons [ph / (mW/m2)]

    # Theoretical propagation of the radiance of the pixel (no MTF, PRNU, DS, bad/dead pixels)
    L = readNc(dir_mine, 'ism_toa_isrf_' + band + '.nc')[ialt, iact]
    I = L * X
    ph = I * Y
    e = min(ph * cfg.QE, cfg.FWC)
    V = e * e2V
    DN = min(max(np.round(V * V2DN), 0), 2 ** cfg.bit_depth - 1)

    # Values of my outputs in the same pixel
    I_mine = readNc(dir_mine, 'ism_toa_optical_' + band + '.nc')[ialt, iact]
    e_mine = readNc(dir_mine, 'ism_toa_e_' + band + '.nc')[ialt, iact]
    DN_mine = readNc(dir_mine, 'ism_toa_' + band + '.nc')[ialt, iact]

    lines.append('%s | %.6e | %.4f | %.4f | %.1f | %.1f | %.4f | %d || %.4f | %.1f | %d' %
                 (band, Y, L, I, ph, e, V, DN, I_mine, e_mine, DN_mine))

for line in lines:
    print(line)
with open(os.path.join(dir_fig, 'ism_unit_conversion.txt'), 'w') as f:
    f.write('\n'.join(lines))

# -------------------------------------------------------------------------------
# 3. System MTF and the 6 contributors. Defining MTF (lowest contributor at Nyquist)
# -------------------------------------------------------------------------------
names = ['Hdiff', 'Hdefoc', 'Hwfe', 'Hdet', 'Hsmear', 'Hmotion', 'Hsys']
labels = ['Diffraction MTF', 'Defocus MTF', 'WFE Aberrations MTF', 'Detector MTF',
          'Smearing MTF', 'Motion blur MTF', 'System MTF']
eps = 1e-6

mtf_lines = []
for band in bands:
    H = [readNc(dir_mine, name + '_' + band + '.nc') for name in names]
    nlines, ncolumns = H[0].shape
    idalt = int(nlines / 2)
    idact = int(ncolumns / 2)

    # Normalised frequencies f/(1/w), same as in mtf.freq2d
    fnAct = np.arange(-0.5, 0.5 - eps, 1 / ncolumns)
    fnAlt = np.arange(-0.5, 0.5 - eps, 1 / nlines)

    for cut in ['Act', 'Alt']:
        fig = plt.figure(figsize=(10, 7))
        for i in range(len(names)):
            if cut == 'Act':
                fn, y = fnAct, H[i][idalt, :]
            else:
                fn, y = fnAlt, H[i][:, idact]
            idx = fn >= 0
            if names[i] == 'Hsys':
                plt.plot(fn[idx], y[idx], '-k', linewidth=2.5, label=labels[i])
            else:
                plt.plot(fn[idx], y[idx], linewidth=1.2, label=labels[i])
        plt.axvline(x=0.5, color='black', linestyle='--', linewidth=2, label='f Nyquist')
        plt.title('System MTF - slice ' + cut.upper() + ' ' + band, fontsize=16)
        plt.xlabel('Spatial frequencies f/(1/w) [-]', fontsize=14)
        plt.ylabel('MTF', fontsize=14)
        plt.xlim([-0.01, 0.52])
        plt.ylim([-0.05, 1.05])
        plt.legend(loc='lower left')
        plt.grid()
        saveas = os.path.join(dir_fig, 'system_mtf_cut' + cut + '_' + band + '.png')
        plt.savefig(saveas)
        plt.close(fig)
        print('Saved image ' + saveas)

    # Values at Nyquist (first element of the frequency vector, f/(1/w) = -0.5, the MTF is symmetric)
    nyq_act = [h[idalt, 0] for h in H]
    nyq_alt = [h[0, idact] for h in H]
    defining_act = labels[int(np.argmin(nyq_act[:-1]))]
    defining_alt = labels[int(np.argmin(nyq_alt[:-1]))]

    mtf_lines.append(band + ' - MTF at Nyquist ACT: ' +
                     ', '.join(names[i] + ' = %.3f' % nyq_act[i] for i in range(len(names))) +
                     ' -> defining: ' + defining_act)
    mtf_lines.append(band + ' - MTF at Nyquist ALT: ' +
                     ', '.join(names[i] + ' = %.3f' % nyq_alt[i] for i in range(len(names))) +
                     ' -> defining: ' + defining_alt)

for line in mtf_lines:
    print(line)
with open(os.path.join(dir_fig, 'ism_mtf_nyquist.txt'), 'w') as f:
    f.write('\n'.join(mtf_lines))