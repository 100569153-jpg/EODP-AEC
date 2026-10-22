
# MAIN FUNCTION TO CALL THE L1C MODULE

from l1c.src.l1c import l1c

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = r'C:/Users/alexe/Downloads/EODP/EODP_code/auxiliary'
# GM dir + L1B dir
indir = r'C:/Users/alexe/Downloads/EODP/EODP-TS-E2E/gm_out/,C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1B/output_AEC_last class'
outdir = r'C:/Users/alexe/Downloads/EODP/EODP_TER_2021/EODP-TS-L1C/output_AEC_last class'

# Initialise the ISM
myL1c = l1c(auxdir, indir, outdir)
myL1c.processModule()
