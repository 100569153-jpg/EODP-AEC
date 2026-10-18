
# LEVEL-1C

from l1c.src.initL1c import initL1c
from common.io.writeToa import writeToa, readToa
from common.io.readGeodetic import readGeodetic, getCorners
import mgrs
import numpy as np
from scipy.interpolate import bisplrep, bisplev
import matplotlib.pyplot as plt
from common.io.l1cProduct import writeL1c
import os
import sys

class l1c(initL1c):

    def __init__(self, auxdir, indir, outdir):
        super().__init__(auxdir, indir, outdir)

    def processModule(self):

        self.logger.info("Start of the L1C Processing Module")

        for band in self.globalConfig.bands:

            self.logger.info("Start of BAND " + band)

            # Read TOA - output of the L1B in Radiances
            # -------------------------------------------------------------------------------
            toa = readToa(self.l1bdir, self.globalConfig.l1b_toa + band + '.nc')
            lat,lon = readGeodetic(self.gmdir, self.globalConfig.gm_geoloc)
            self.checkSize(lat,toa)

            # L1C reprojection onto the MGRS grid
            # -------------------------------------------------------------------------------
            lat_l1c, lon_l1c, toa_l1c = self.l1cProjtoa(lat, lon, toa, band)

            # Write output TOA
            # -------------------------------------------------------------------------------
            writeL1c(self.outdir, self.globalConfig.l1c_toa + band, lat_l1c, lon_l1c, toa_l1c)

            self.logger.info("End of BAND " + band)

        self.logger.info("End of the L1C Module!")


    def l1cProjtoa(self, lat, lon, toa, band):
        '''
        This function reprojects the L1B radiances into the MGRS grid.

        The MGRS reference system
        https://www.bluemarblegeo.com/knowledgebase/calculator-2020/Military_Grid_Reference_System_(MGRS).htm
        MGRS: '31REQ4367374067'
        31 is the UTM zone, R is the UTM latitude band; EQ are the MGRS column and row band letters
        43673 is the MGRS Easting (5 dig); 74067 is the MGRS Northing (5dig)

        Python mgrs library documentation
        https://pypi.org/project/mgrs/

        :param lat: L1B latitudes [deg]
        :param lon: L1B longitudes [deg]
        :param toa: L1B radiances
        :param band: band
        :return: L1C radiances, L1C latitude and longitude in degrees
        '''
        #TODO
        tck = bisplrep(lat, lon, toa)
        m = mgrs.MGRS()
        mgrs_tiles = set([])

        for ii in range (toa.shape[0]): #100
            for jj in range (toa.shape[1]):  # 150
                auxi = str(m.toMGRS(lat[ii, jj], lon[ii, jj], MGRSPrecision=self.l1cConfig.mgrs_tile_precision))
                mgrs_tiles.add(auxi)

        mgrs_tiles = list(mgrs_tiles)

        toa_l1c = np.zeros(len(mgrs_tiles))
        lat_l1c = np.zeros(len(mgrs_tiles))
        lon_l1c = np.zeros(len(mgrs_tiles))

        for ii in range (len(mgrs_tiles)):
            (lat_l1c[ii], lon_l1c[ii]) = m.toLatLon(mgrs_tiles[ii], inDegrees=True)
            toa_l1c[ii] = bisplev(lat_l1c[ii], lon_l1c[ii], tck)

        # Plot the L1B and L1C grids and the L1C TOA
        if self.l1cConfig.plotL1cGrid:
            self.plotL1cGrid(lat, lon, lat_l1c, lon_l1c, toa_l1c, band)
        return lat_l1c, lon_l1c, toa_l1c

    def checkSize(self, lat,toa):
        '''
        Check the sizes of the input radiances and geodetic coordinates.
        If they don't match, exit.
        :param lat: Latitude 2D matrix
        :param toa: Radiance 2D matrix
        :return: NA
        '''
        #TODO
        if lat.shape != toa.shape:
            self.logger.error("Sizes of the geodetic coordinates " + str(lat.shape) +
                              " and the TOA " + str(toa.shape) + " do not match")
            sys.exit(1)

    def plotL1cGrid(self, lat, lon, lat_l1c, lon_l1c, toa_l1c, band):
        '''
        Plot of the L1B (irregular) and L1C (MGRS) grids and of the L1C TOA
        '''
        # L1B and L1C grids in the same plot
        fig = plt.figure(figsize=(10, 7))
        plt.plot(lon.flatten(), lat.flatten(), '.b', markersize=2, label='L1B grid')
        plt.plot(lon_l1c, lat_l1c, '.r', markersize=2, label='L1C grid (MGRS 100 m)')
        plt.title('L1B and L1C grids ' + band, fontsize=16)
        plt.xlabel('Longitude [deg]', fontsize=14)
        plt.ylabel('Latitude [deg]', fontsize=14)
        plt.legend()
        plt.grid()
        plt.savefig(os.path.join(self.outdir, 'l1b_l1c_grids_' + band + '.png'))
        plt.close(fig)

        # L1C TOA
        fig = plt.figure(figsize=(10, 7))
        sc = plt.scatter(lon_l1c, lat_l1c, c=toa_l1c, s=4, cmap='jet')
        plt.colorbar(sc, label='TOA [mW/m2/sr]')
        plt.title('L1C TOA ' + band, fontsize=16)
        plt.xlabel('Longitude [deg]', fontsize=14)
        plt.ylabel('Latitude [deg]', fontsize=14)
        plt.grid()
        plt.savefig(os.path.join(self.outdir, 'l1c_toa_' + band + '.png'))
        plt.close(fig)