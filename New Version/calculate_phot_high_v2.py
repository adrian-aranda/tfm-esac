import glob
import os
import numpy as np

from astropy.io import fits
from astropy.wcs import WCS, utils
from astropy.coordinates import SkyCoord
from astropy import units as u

from astropy.convolution import convolve, Box2DKernel, Gaussian2DKernel
from astropy.visualization import PercentileInterval, ManualInterval, ImageNormalize, AsinhStretch, LogStretch, LinearStretch

#import aplpy

from photutils import SkyCircularAnnulus, SkyCircularAperture, aperture_photometry
from regions import CircleSkyRegion

import matplotlib.pylab as plt
from matplotlib.patches import Circle

from commons import exec_task
from commons import sasinit

def get_coords(odf_dir):
    logs_list = glob.glob("{}/logs/rad_prof*".format(odf_dir))
    aux = False
    aux_r = []
    circle = ""
    for log in logs_list:
        if not aux:
            with open(log, "r") as f:
                for line in f:
                    if "CIRCLE: " in line:
                        #circle = line.split(" ")[1]
                        circle = line.split("- ")[1].split(" ")[1]
                        #print(circle)
                if circle != "":
                    aux_r.append(float(circle.split(',')[2]))
                    #aux = True
    RA = float(circle.split(',')[0])
    DEC = float(circle.split(',')[1])
    r = max(aux_r)
    print(RA, DEC, r)
    return [RA, DEC, r]


def calc_radial_profile(fitsfile, center, rstart, rend, rstep, verbose=False, detmaskfile=None, plot=True):
    """

    Utility function to calculate the radial profile from an image `fitsfile` at a `center`

    """
    #
    if (not os.path.isfile(fitsfile)):
        print(f"ERROR. FITS file {fitsfile} not found. Cannot continue.")
        return None
    #
    qhdu = fits.open(fitsfile)
    wcs = WCS(qhdu[0].header)
    #
    # if detmaskfile is provided then will use it for detector mask
    #
    doMask = False
    if (detmaskfile != None):
        if (not os.path.isfile(detmaskfile)):
            print(f"Warning. Detector mask file {detmaskfile} not found. Will not use detector mask!")
            doMask = False
        else:
            det = fits.open(detmaskfile)
            detmask = det['MASK']
            # need the WCS
            wcs_det = WCS(detmask.header)
            doMask = True
    #
    if (not isinstance(center, SkyCoord)):
        print(f"EROOR: the input radial profile centre is not SkyCoord object. Cannot continue.")
        return None
    #
    j = 0
    rx = rstart
    counts = []
    counts_err = []
    rmid = []
    #
    emtpy = False
    while rx < r_end:
        r0 = rstart + rstep * j
        rx = rstart + rstep * (j + 1)
        # the mid point, can be better the mid area point
        rmid.append((r0.value + rx.value) / 2.0)
        if (j == 0):
            xap = SkyCircularAperture(center, rx)
            photo = aperture_photometry(qhdu[0].data, xap, wcs=wcs)
            if (doMask):
                masked = aperture_photometry(detmask.data, xap, wcs=wcs_det)
        else:
            xap = SkyCircularAnnulus(center, r0, rx)
            photo = aperture_photometry(qhdu[0].data, xap, wcs=wcs)
            if (doMask):
                masked = aperture_photometry(detmask.data, xap, wcs=wcs_det)
        #
        ap_area = xap.to_pixel(wcs).area
        good_area = ap_area
        if (doMask):
            good_area = masked['aperture_sum'][0]
        # compare the two annuli areas: with and without bad pixels
        if (verbose):
            print(
                f"Annulus: {r0:.2f},{rx:.2f},geometric area: {ap_area:.1f} pixels,non-masked area {good_area:.1f} pixels, ratio: {ap_area / good_area:.2f}")
        # taking into account the masked pixels
        if (good_area == 0.0):
            counts.append(float('nan'))
            counts_err.append(float('nan'))
        else:
            counts.append(photo['aperture_sum'][0] / good_area)
            counts_err.append(np.sqrt(photo['aperture_sum'][0]) / good_area)

        j += 1
    #
    # convert the results in numpy arrays
    #
    rmid = np.array(rmid)
    counts = np.array(counts)
    counts_err = np.array(counts_err)
    #
    # convert per pixel to per arcsec^2
    pix_area = utils.proj_plane_pixel_area(wcs) * 3600.0 * 3600.0  # in arcsec^2
    counts = counts / pix_area
    counts_err = counts_err / pix_area
    #
    if (plot):
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.errorbar(rmid, counts, xerr=rstep.value / 2.0, yerr=counts_err)
        ax.set_xscale('linear')
        ax.set_yscale('log')
        ax.set_xlabel('Radial distance (arcsec)')
        ax.set_ylabel(r'Counts/arcsec$^2$')
        ax.grid()
        ax.set_title(f"Radial profile");
    qhdu.close()
    if (doMask):
        det.close()
    return rmid, counts, counts_err

def psf_gen(center, energy, box, psf_out):
    psfgen = f'psfgen image={fits_image} withimage=yes instrument=PN level=ELLBETA energy={energy} ' + \
             f'x={center.ra.value} y={center.dec.value} coordtype=EQPOS xsize={box} ysize={box} output={psf_out}'
    status = exec_task(psfgen)
    if (status != 0):
        raise RuntimeError

if __name__ == '__main__':

    # Initialize SAS
    sasinit()

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


    wdir = "/home/aaranda/tfm/obsid"

    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data

    bin_size = 80
    pi = [500, 2000, 4500, 10000]

    error_obsid = []
    count = 1
    #obsid_list = ['0830190501']
    for obsid in obsid_list:

        try:

            # Find target name
            for row in data:
                if row[5] == obsid:
                    target = row[0]

            print("Executing {} of {}...".format(count, len(obsid_list)))
            count += 1
            odf_dir = "{}/{}".format(wdir, obsid)

            os.chdir(odf_dir)
            cif_file = "{}/ccf.cif".format(odf_dir)
            os.environ['SAS_CCF'] = cif_file
            SUM_SAS_file = glob.glob("*SUM.SAS")[0]
            os.environ['SAS_ODF'] = SUM_SAS_file

            coords = get_coords(odf_dir)
            center = SkyCoord(coords[0], coords[1], unit=(u.deg, u.deg), frame='icrs')
            r_start = 0.0 * u.arcsec
            r_end = 4.0 * u.arcmin
            r_step = 6.0 * u.arcsec

            detmask_file = '{}/detfile_high.fits'.format(odf_dir)
            det = fits.open(detmask_file)
            detmask = det['MASK']
            wcs_det = WCS(detmask.header)

            fits_image = '{}/images/image_filtered_high.fits'.format(odf_dir)
            # if not os.path.isfile('{}/images/image_filtered_high_clean.fits'.format(odf_dir)):
            #     fits_image = '{}/images/image_filtered_high.fits'.format(odf_dir)
            # else:
            #     fits_image = '{}/images/image_filtered_high_clean.fits'.format(odf_dir)

            hdu = fits.open(fits_image)
            wcs = WCS(hdu[0].header)
            g2_kernel = Gaussian2DKernel(2)
            smoothed_data_g2 = convolve(hdu[0].data, g2_kernel, mask=np.logical_not(detmask.data)) * detmask.data

            fig = plt.figure(figsize=(10, 10), dpi=100)
            pp = 99.9  # colour cut percentage

            ax = fig.add_subplot(111, projection=wcs)
            #ax.set_title("Gaussian smoothed image")
            norm_xmm = ImageNormalize(smoothed_data_g2, interval=ManualInterval(vmin=0.01, vmax=100.0),
                                      stretch=LogStretch())
            # norm_xmm = ImageNormalize(smoothed_data_g2,interval=PercentileInterval(pp), stretch=AsinhStretch())
            ax.imshow(smoothed_data_g2, cmap=plt.cm.hot, norm=norm_xmm, origin='lower', interpolation='nearest')
            ax.xlabel = 'RA'
            ax.ylabel = 'Dec'
            ax.set_xlabel('RA')
            ax.set_ylabel('DEC')
            #
            # only show the last aperture
            #
            circle_sky = CircleSkyRegion(center=center, radius=r_end)
            pix_reg = circle_sky.to_pixel(wcs)
            pix_reg.plot(ax=ax, edgecolor='yellow')
            plt.savefig('/home/aaranda/tfm/results_v2/{}/{}/smoothed_g2_image_high.png'.format(target, obsid))
            plt.close(fig)


            (x, y, yerr) = calc_radial_profile(fits_image, center, r_start, r_end, r_step, verbose=False,
                                               detmaskfile=detmask_file, plot=False)

            energy = 5000  # at 5 keV
            box = 2 * int(r_end.to(u.arcsec).value) + 1
            psf_out = '{}/psf_ellbeta_{}_{}pix.fits'.format(odf_dir, energy, box)
            psf_gen(center, energy, box, psf_out)

            fig = plt.figure(figsize=(10, 10), dpi=100)
            pp = 99.9  # colour cut percentage

            psf_hdu = fits.open(psf_out)
            wcs_psf = WCS(psf_hdu[0].header)

            ax = fig.add_subplot(111, projection=wcs_psf)
            #ax.set_title(f"PSFGEN image at {energy / 1000:.1f} keV")
            norm_xmm = ImageNormalize(psf_hdu[0].data, stretch=LogStretch())
            ax.imshow(psf_hdu[0].data, cmap=plt.cm.hot, norm=norm_xmm, origin='lower', interpolation='nearest')
            circle_sky = CircleSkyRegion(center=center, radius=r_end)
            pix_reg = circle_sky.to_pixel(wcs_psf)
            pix_reg.plot(ax=ax, edgecolor='cyan')
            ax.xlabel = 'RA'
            ax.ylabel = 'Dec'
            ax.set_xlabel('RA')
            ax.set_ylabel('DEC')
            plt.savefig('/home/aaranda/tfm/results_v2/{}/{}/theorical_psf_high.png'.format(target, obsid))
            plt.close(fig)

            (psf_mid, psf_counts, psf_counts_err) = \
                calc_radial_profile(psf_out, center, r_start, r_end, r_step, verbose=False, detmaskfile=None, plot=False)

            #
            # normalise the source
            #
            jnorm = next((i for i, yy in enumerate(y) if (yy > 0.0)), None)
            #
            if (jnorm > 0):
                print("Warning: the central radial bin is masked (zero area) or has zero counts.")
                print(
                    f"The first non-zero radial bin is with index {jnorm}, bin start at {r_start + r_step * jnorm} arcsec")
            norm_counts = y / y[jnorm]
            norm_counts_err = yerr / y[jnorm]
            back = np.mean(norm_counts[-3:])  # the mean of the last 3 radial points
            #
            # and normalise the PSF
            #
            norm_psf_counts = psf_counts / psf_counts[jnorm]
            #

            fig, ax = plt.subplots(figsize=(10, 8))
            # ax.errorbar(rmid,counts,xerr=r_step.value/2.0,yerr=counts_err)
            # ax.errorbar(rmid,counts_arcsec2,xerr=r_step.value/2.0,yerr=counts_err_arcsec2,label='Source')
            ax.errorbar(x, norm_counts, xerr=r_step.value / 2.0, yerr=norm_counts_err, label='Fuente')
            # ax.plot(psf_mid,norm_psf_counts,label=f'PSF at {energy/1000:.2f} keV')
            ax.plot(psf_mid, norm_psf_counts + back, label='PSF + background', color='red')
            ax.axhline(back, color='gray', linestyle="--", label='Background')
            ax.set_xscale('linear')
            ax.set_yscale('log')
            ax.set_xlabel('Radial distance (arcsec)')
            ax.set_ylabel(r'Normalised counts/arcsec$^2$')
            ax.grid()
            #ax.set_title(f"Radial profile taking into account the bad pixels and CCD chip gaps")
            ax.legend();
            plt.savefig('/home/aaranda/tfm/results_v2/{}/{}/radial_profile_high.png'.format(target, obsid))
            plt.close(fig)
        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass

    print(error_obsid)