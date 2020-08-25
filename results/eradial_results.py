import os
import numpy as np
import glob
import matplotlib
#matplotlib.use('Agg')

from astropy.io import fits
from astropy.wcs import WCS, utils
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.table import Table


# %matplotlib inline
import matplotlib.pylab as plt

from photutils import SkyCircularAperture, SkyCircularAnnulus, aperture_photometry



def get_bl_lac(obsid):
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    for row in data:
        if row[5] == obsid:
            bl_lac = row[0]
    return bl_lac


if __name__ == '__main__':

    # Good obsid_lits extracter from find_valid_targets.py
    obsid_list = ['0142270101', '0300480201', '0300480301', '0401060201', '0502630201', '0679380701', '0761500201',
                  '0651360401', '0800732801', '0762870401', '0122520201', '0674330201', '0653040101', '0744412401',
                  '0783881001', '0302580401', '0502430201', '0502430701', '0693010401', '0106060601', '0112550801',
                  '0112551101', '0721890101', '0148250201', '0300140101', '0149880101', '0303930101', '0650380201',
                  '0693741001', '0153170101', '0084140101', '0084140501', '0655343842', '0002970201', '0604210201',
                  '0604210301', '0151490101', '0785110401', '0152900201', '0740820401', '0123100101', '0123100201',
                  '0670040101', '0761112401', '0803240801', '0830190501', '0303820301', '0783520201', '0652810201',
                  '0152460301', '0305750601', '0551750301', '0600920201', '0112830201', '0112830501', '0104860501',
                  '0124900101', '0692510101', '0604830201', '0100240101', '0100240201', '0804272701', '0722140101',
                  '0722140401', '0800270601', '0790380501', '0790380601', '0790380801', '0790381401', '0790381501',
                  '0790380901', '0761100101', '0761100201', '0761100301', '0761100401', '0761101001', '0744640101',
                  '0553561101', '0655346840', '0673000136', '0405380701', '0782350501']

    error_obsid = []

    obsid_list = ["0002970201"]
    for obsid in obsid_list:

        try:

            wdir = "/home/aaranda/tfm/obsid"
            odf_dir = "{}/{}".format(wdir, obsid)

            target = get_bl_lac(obsid)

            # From eradial

            # LOW
            radprof_low = "{}/radprof_low.ds".format(odf_dir)
            hdu_list = fits.open(radprof_low, memmap=True)
            evt_data = Table(hdu_list[1].data)

            print(evt_data['RPROF'])
            print(evt_data['FIT_RPSF'])

            fig, ax = plt.subplots(figsize=(10, 10))
            # ax.errorbar(rmid,counts,xerr=r_step.value/2.0,yerr=counts_err)

            # ax.errorbar(rmid,counts_arcsec2,xerr=r_step.value/2.0,yerr=counts_err_arcsec2, fmt='d', color='blue', ecolor='blue')

            ax.errorbar(evt_data['RAD_LO'], evt_data['RPROF'], yerr= evt_data['RPROF_ERR'], fmt='v', color='red',
                        ecolor='red')
            ax.plot(evt_data['RAD_LO'], evt_data['FIT_RPSF'], color='black', linewidth=2)
            ax.set_xscale('linear')
            ax.set_yscale('log')
            ax.set_xlabel('Radio (arcsec)', fontsize=18)
            ax.tick_params(axis='both', which='major', labelsize='x-large')
            ax.set_ylabel(r'Cuentas/arcsec$^2$', fontsize=18)
            ax.grid()
            # ax.set_title(f"Radial profile")
            # ax.legend(["PSF", "Photometry", "Eradial"], fontsize='x-large')
            ax.legend(["PSF", "Fuente"], fontsize='xx-large')
            plt.savefig('/home/aaranda/tfm/results/{}/{}/radprof_low.png'.format(target, obsid))
            plt.close(fig)

            # # HIGH
            # radprof_high = "{}/radprof_high.ds".format(odf_dir)
            # hdu_list = fits.open(radprof_high, memmap=True)
            # evt_data = Table(hdu_list[1].data)
            #
            # fig, ax = plt.subplots(figsize=(10, 10))
            # # ax.errorbar(rmid,counts,xerr=r_step.value/2.0,yerr=counts_err)
            #
            # # ax.errorbar(rmid,counts_arcsec2,xerr=r_step.value/2.0,yerr=counts_err_arcsec2, fmt='d', color='blue', ecolor='blue')
            #
            # ax.errorbar(evt_data['RAD_LO'], evt_data['RPROF'], yerr=evt_data['RPROF_ERR'], fmt='v', color='red',
            #             ecolor='red')
            # ax.plot(evt_data['RAD_LO'], evt_data['FIT_RPSF'], color='black', linewidth=2)
            # ax.set_xscale('log')
            # ax.set_yscale('log')
            # ax.set_xlabel('Radio (arcsec)', fontsize=18)
            # ax.tick_params(axis='both', which='major', labelsize=14)
            # ax.set_ylabel(r'Cuentas/arcsec$^2$', fontsize=18)
            # ax.grid()
            # # ax.set_title(f"Radial profile")
            # ax.legend(["PSF", "Fuente"], fontsize='x-large')
            # plt.savefig('/home/aaranda/tfm/results/{}/{}/radprof_high.png'.format(target, obsid))
            # plt.close(fig)

        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass

    print(error_obsid)