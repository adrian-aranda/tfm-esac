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

    obsid = "0604210201"

    wdir = "/home/aaranda/tfm/obsid"
    odf_dir = "{}/{}".format(wdir, obsid)

    target = get_bl_lac(obsid)

    # From eradial

    # LOW
    radprof_low = "{}/radprof_low.ds".format(odf_dir)
    hdu_list = fits.open(radprof_low, memmap=True)
    evt_data = Table(hdu_list[1].data)

    fig, ax = plt.subplots(figsize=(10, 10))
    # ax.errorbar(rmid,counts,xerr=r_step.value/2.0,yerr=counts_err)

    # ax.errorbar(rmid,counts_arcsec2,xerr=r_step.value/2.0,yerr=counts_err_arcsec2, fmt='d', color='blue', ecolor='blue')

    ax.errorbar(evt_data['RAD_LO'], evt_data['RPROF'], yerr= evt_data['RPROF_ERR'], fmt='v', color='red',
                ecolor='red')
    ax.plot(evt_data['RAD_LO'], evt_data['FIT_RPSF'], color='black', linewidth=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Radio (arcsec)', fontsize=18)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.set_ylabel(r'Cuentas/arcsec$^2$', fontsize=18)
    ax.grid()
    # ax.set_title(f"Radial profile")
    # ax.legend(["PSF", "Photometry", "Eradial"], fontsize='x-large')
    ax.legend(["PSF", "Fuente"], fontsize='x-large')
    plt.savefig('/home/aaranda/tfm/results/{}/{}/radprof_low.png'.format(target, obsid))
    plt.close(fig)

    # HIGH
    radprof_high = "{}/radprof_high.ds".format(odf_dir)
    hdu_list = fits.open(radprof_high, memmap=True)
    evt_data = Table(hdu_list[1].data)

    fig, ax = plt.subplots(figsize=(10, 10))
    # ax.errorbar(rmid,counts,xerr=r_step.value/2.0,yerr=counts_err)

    # ax.errorbar(rmid,counts_arcsec2,xerr=r_step.value/2.0,yerr=counts_err_arcsec2, fmt='d', color='blue', ecolor='blue')

    ax.errorbar(evt_data['RAD_LO'], evt_data['RPROF'], yerr=evt_data['RPROF_ERR'], fmt='v', color='red',
                ecolor='red')
    ax.plot(evt_data['RAD_LO'], evt_data['FIT_RPSF'], color='black', linewidth=2)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Radio (arcsec)', fontsize=18)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.set_ylabel(r'Cuentas/arcsec$^2$', fontsize=18)
    ax.grid()
    # ax.set_title(f"Radial profile")
    ax.legend(["PSF", "Fuente"], fontsize='x-large')
    plt.savefig('/home/aaranda/tfm/results/{}/{}/radprof_high.png'.format(target, obsid))
    plt.close(fig)
