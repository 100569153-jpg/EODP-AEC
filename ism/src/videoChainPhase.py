
from ism.src.initIsm import initIsm
import numpy as np
from common.plot.plotMat2D import plotMat2D
from common.plot.plotF import plotF

class videoChainPhase(initIsm):

    def __init__(self, auxdir, indir, outdir):
        super().__init__(auxdir, indir, outdir)

    def compute(self, toa, band):
        self.logger.info("EODP-ALG-ISM-3000: Video Chain")

        # Electrons to Voltage - read-out & amplification
        # -------------------------------------------------------------------------------
        self.logger.info("EODP-ALG-ISM-3010: Electrons to Voltage – Read-out and Amplification")
        toa = self.electr2Volt(toa,
                         self.ismConfig.OCF,
                         self.ismConfig.ADC_gain)

        self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [V]")

        # Digitisation
        # -------------------------------------------------------------------------------
        self.logger.info("EODP-ALG-ISM-3020: Voltage to Digital Numbers – Digitisation")
        toa = self.digitisation(toa,
                          self.ismConfig.bit_depth,
                          self.ismConfig.min_voltage,
                          self.ismConfig.max_voltage)

        self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [DN]")

        # Plot
        if self.ismConfig.save_vcu_stage:
            saveas_str = self.globalConfig.ism_toa_vcu + band
            title_str = 'TOA after the VCU phase [DN]'
            xlabel_str='ACT'
            ylabel_str='ALT'
            plotMat2D(toa, title_str, xlabel_str, ylabel_str, self.outdir, saveas_str)

            idalt = int(toa.shape[0]/2)
            saveas_str = saveas_str + '_alt' + str(idalt)
            plotF([], toa[idalt,:], title_str, xlabel_str, ylabel_str, self.outdir, saveas_str)

        return toa

    def electr2Volt(self, toa, OCF, gain_adc):
        """
        Electron to Volts conversion.
        Simulates the read-out and the amplification
        (multiplication times the gain).
        :param toa: input toa in [e-]
        :param OCF: Output Conversion factor [V/e-]
        :param gain_adc: Gain of the Analog-to-digital conversion [-]
        :return: output toa in [V]
        """
        #TODO
        #1. Convert electrons to readout node voltage [V] using Output Conversion Factor (OCF)
        #2. Apply Analog-to-Digital Converter amplification gain
        toa_v = toa * OCF * gain_adc
        return toa

    def digitisation(self, toa, bit_depth, min_voltage, max_voltage):
        """
        Digitisation - conversion from Volts to Digital counts
        :param toa: input toa in [V]
        :param bit_depth: bit depth
        :param min_voltage: minimum voltage
        :param max_voltage: maximum voltage
        :return: toa in digital counts
        """
        #TODO
        #1. Calculate maximum dynamic digital count value (e.g., 2^12 - 1 = 4095 for 12-bit)
        max_dn = (2 ** bit_depth) - 1

        # 2. Scale voltage range [min_voltage, max_voltage] linearly to digital counts [0, max_dn]
        toa_dn = (toa - min_voltage) * (max_dn / (max_voltage - min_voltage))

        # 3. Quantize voltage values to integer levels (floor truncation)
        toa_dn = np.floor(toa_dn)

        # 4. Saturate (clip) signal below min digital count (0) or above max digital count (max_dn)
        toa_dn = np.clip(toa_dn, 0, max_dn)
        return toa_dn

