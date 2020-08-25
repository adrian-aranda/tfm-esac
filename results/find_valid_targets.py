import glob
import os

from astropy.io import fits
from astropy.coordinates import SkyCoord

def get_catalog_coords(obsid):
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    RA = []
    DEC = []
    for row in data:
        if row[5] == obsid:
                RA = row[1]
                DEC = row[2]
                target = row[0]
    return [RA, DEC, target]


def build_dir(target, obsid):
    results_dir = "/home/aaranda/tfm/results_v2"
    target_dir = results_dir + "/" + target
    obsid_dir = target_dir + "/" + obsid
    if (not os.path.isdir(target_dir)):
        os.mkdir(target_dir)
        print("{} created".format(target_dir))
    if (not os.path.isdir(obsid_dir)):
        os.mkdir(obsid_dir)
        print("{}/ created".format(obsid_dir))


if __name__ == '__main__':

    wdir = "/home/aaranda/tfm/obsid"

    # Check for obsid in catalog that are not PrimeSmallWindow
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    obsid_list = []
    for row in data:
        if row[10] != "PrimeSmallWindow":
            obsid_list.append(row[5])

    offset = []
    targets = []
    good_targets = []
    good_obsid = []
    count = 0
    for obsid in obsid_list:
        pps_dir = wdir + "/" + obsid + "/pps"
        os.chdir(pps_dir)
        events_file = glob.glob("*PIEVLI0000.fits")[0]
        hdul = fits.open(events_file)

        # Get target coordinates and target name
        [RA_OBJ, DEC_OBJ, target] = get_catalog_coords(obsid)

        # Get boresight coordinates of the obsid
        RA_NOM = float(hdul[0].header["RA_NOM"])
        DEC_NOM = float(hdul[0].header["DEC_NOM"])

        # Calculate offset
        c_OBJ = SkyCoord(RA_OBJ, DEC_OBJ, unit='deg', frame='icrs')
        c_NOM = SkyCoord(RA_NOM, DEC_NOM, unit='deg', frame='icrs')
        sep = c_OBJ.separation(c_NOM)

        targets.append(target)
        offset.append(float(sep.arcmin))

        if sep.arcmin < 10:
            good_targets.append(target)
            good_obsid.append(obsid)
            #print(target, obsid)
            count += 1

            # Creates directories for results
            build_dir(target, obsid)

    print(good_obsid)
    print("The total of obsid is: {}".format(count))
        # print(target, count, obsid, RA_OBJ, DEC_OBJ, RA_NOM, DEC_NOM, sep.arcmin)

    # Get good target list
    output = []
    for x in good_targets:
        if x not in output:
            output.append(x)
    print(output)

    print("The total of target is: {}".format(len(output)))


