
from ism.src.initIsm import initIsm
import numpy as np
from common.io.writeToa import writeToa
from common.plot.plotMat2D import plotMat2D
from common.plot.plotF import plotF

class detectionPhase(initIsm):

    def __init__(self, auxdir, indir, outdir):
        super().__init__(auxdir, indir, outdir)

        # Initialise the random see for the PRNU and DSNU
        np.random.seed(self.ismConfig.seed)


    def compute(self, toa, band):

        self.logger.info("EODP-ALG-ISM-2000: Detection stage")

        # Irradiance to photons conversion
        # -------------------------------------------------------------------------------
        self.logger.info("EODP-ALG-ISM-2010: Irradiances to Photons")
        area_pix = self.ismConfig.pix_size * self.ismConfig.pix_size # [m2]
        toa = self.irrad2Phot(toa, area_pix, self.ismConfig.t_int, self.ismConfig.wv[int(band[-1])])

        self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [ph]")

        # Photon to electrons conversion
        # -------------------------------------------------------------------------------
        self.logger.info("EODP-ALG-ISM-2030: Photons to Electrons")
        toa = self.phot2Electr(toa, self.ismConfig.QE)

        self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [e-]")

        if self.ismConfig.save_after_ph2e:
            saveas_str = self.globalConfig.ism_toa_e + band
            writeToa(self.outdir, saveas_str, toa)

        # PRNU
        # -------------------------------------------------------------------------------
        if self.ismConfig.apply_prnu:

            self.logger.info("EODP-ALG-ISM-2020: PRNU")
            toa = self.prnu(toa, self.ismConfig.kprnu)

            self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [e-]")

            if self.ismConfig.save_after_prnu:
                saveas_str = self.globalConfig.ism_toa_prnu + band
                writeToa(self.outdir, saveas_str, toa)

        # Dark-signal
        # -------------------------------------------------------------------------------
        if self.ismConfig.apply_dark_signal:

            self.logger.info("EODP-ALG-ISM-2020: Dark signal")
            toa = self.darkSignal(toa, self.ismConfig.kdsnu, self.ismConfig.T, self.ismConfig.Tref,
                                  self.ismConfig.ds_A_coeff, self.ismConfig.ds_B_coeff)

            self.logger.debug("TOA [0,0] " +str(toa[0,0]) + " [e-]")

            if self.ismConfig.save_after_ds:
                saveas_str = self.globalConfig.ism_toa_ds + band
                writeToa(self.outdir, saveas_str, toa)

        # Bad/dead pixels
        # -------------------------------------------------------------------------------
        if self.ismConfig.apply_bad_dead:

            self.logger.info("EODP-ALG-ISM-2050: Bad/dead pixels")
            toa = self.badDeadPixels(toa,
                               self.ismConfig.bad_pix,
                               self.ismConfig.dead_pix,
                               self.ismConfig.bad_pix_red,
                               self.ismConfig.dead_pix_red)


        # Write output TOA
        # -------------------------------------------------------------------------------
        if self.ismConfig.save_detection_stage:
            saveas_str = self.globalConfig.ism_toa_detection + band

            writeToa(self.outdir, saveas_str, toa)

            title_str = 'TOA after the detection phase [e-]'
            xlabel_str='ACT'
            ylabel_str='ALT'
            plotMat2D(toa, title_str, xlabel_str, ylabel_str, self.outdir, saveas_str)

            idalt = int(toa.shape[0]/2)
            saveas_str = saveas_str + '_alt' + str(idalt)
            plotF([], toa[idalt,:], title_str, xlabel_str, ylabel_str, self.outdir, saveas_str)

        return toa


    def irrad2Phot(self, toa, area_pix, tint, wv):
        """
        Conversion of the input Irradiances to Photons
        :param toa: input TOA in irradiances [mW/m2]
        :param area_pix: Pixel area [m2]
        :param tint: Integration time [s]
        :param wv: Central wavelength of the band [m]
        :return: Toa in photons
        """
        #TODO
        h = self.constants.h_planck
        c = self.constants.speed_light

        # Single photon energy E = (h * c) / wavelength [Joules]
        e_photon = (h * c) / wv

        # Incident energy per pixel [Joules] (1e-3 converts mW/m2 to W/m2)
        energy_pixel = ((toa/1000) * 1e-3) * area_pix * tint

        # Total photons = Energy / Photon energy
        toa_ph = energy_pixel / e_photon

        return toa_ph

    def phot2Electr(self, toa, QE):
        """
        Conversion of photons to electrons
        :param toa: input TOA in photons [ph]
        :param QE: Quantum efficiency [e-/ph]
        :return: toa in electrons
        """
        #TODO
        #1. Convert photons to electrons via Quantum Efficiency
        toae = toa * QE

        #2. Apply Full Well Capacity (FWC) saturation limit
        toae = np.minimum(toae, self.ismConfig.FWC)
        return toae

    def badDeadPixels(self, toa,bad_pix,dead_pix,bad_pix_red,dead_pix_red):
        """
        Bad and dead pixels simulation
        :param toa: input toa in [e-]
        :param bad_pix: Percentage of bad pixels in the CCD [%]
        :param dead_pix: Percentage of dead pixels in the CCD [%]
        :param bad_pix_red: Reduction in the quantum efficiency for the bad pixels [-, over 1]
        :param dead_pix_red: Reduction in the quantum efficiency for the dead pixels [-, over 1]
        :return: toa in e- including bad & dead pixels
        """
        #TODO
        toa[:, 5] = toa[:, 5] * (1 - bad_pix_red)
        ncolumns = toa.shape[1]

        # 1. Convert percentage [%] of affected detector columns into integer counts
        nbad = int(np.round(ncolumns * (bad_pix / 100.0)))
        ndead = int(np.round(ncolumns * (dead_pix / 100.0)))

        # 2. Select distinct columns for bad and dead pixels (if percentage > 0)
        if nbad > 0 or ndead > 0:
            # Pick unique random column indices across the 150 columns
            selected_cols = np.random.choice(ncolumns, size=nbad + ndead, replace=False)
            bad_cols = selected_cols[:nbad]
            dead_cols = selected_cols[nbad:]

            # Apply signal reduction factor (1 - reduction) across all lines for bad pixels
            for col in bad_cols:
                toa[:, col] = toa[:, col] * (1.0 - bad_pix_red)

            # Apply signal reduction factor for dead pixels (1 - 1.0 = 0 signal)
            for col in dead_cols:
                toa[:, col] = toa[:, col] * (1.0 - dead_pix_red)
        return toa

    def prnu(self, toa, kprnu):
        """
        Adding the PRNU effect
        :param toa: TOA pre-PRNU [e-]
        :param kprnu: multiplicative factor to the standard normal deviation for the PRNU
        :return: TOA after adding PRNU [e-]
        """
        #TODO
        #1. Standard normal distribution across all detector columns (150 pixels)
        prnu_eff = np.random.normal(0, 1, toa.shape[1])

        # 2. PRNU factor for each column: PRNU(act) = norm(0, 1) * kPRNU
        prnu_factor = prnu_eff * kprnu

        # 3. Apply time-invariant multiplicative gain across all lines: Ne-(:, act) = Ne-(:, act) * (1 + PRNU(act))
        toa_prnu = toa * (1.0 + prnu_factor)

        return toa_prnu


    def darkSignal(self, toa, kdsnu, T, Tref, ds_A_coeff, ds_B_coeff):
        """
        Dark signal simulation
        :param toa: TOA in [e-]
        :param kdsnu: multiplicative factor to the standard normal deviation for the DSNU
        :param T: Temperature of the system
        :param Tref: Reference temperature of the system
        :param ds_A_coeff: Empirical parameter of the model 7.87 e-
        :param ds_B_coeff: Empirical parameter of the model 6040 K
        :return: TOA in [e-] with dark signal
        """
        #TODO
        #1. Get number of detector columns (ACT direction)
        ncolumns = toa.shape[1]

        # 2. DSNU spatial component (positive modulus of standard normal distribution)
        dsnu = np.abs(np.random.standard_normal(ncolumns)) * kdsnu

        # 3. Mean dark signal thermal component (Sd)
        sd = ds_A_coeff * ((T / Tref) ** 3) * np.exp(-ds_B_coeff * ((1.0 / T) - (1.0 / Tref)))

        # 4. Total dark signal per column (time-invariant across all lines)
        ds = sd * (1.0 + dsnu)

        # 5. Add dark signal to the input electron image (additive noise)
        toa_ds = toa + ds
        return toa
