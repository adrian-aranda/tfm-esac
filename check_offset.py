import glob
import os

from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

wdir = "/home/aaranda/tfm/obsid"

bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
data = bll_catalog[1].data
obsid_list = []
for row in data:
    obsid_list.append(row[5])

count = 0
for obsid in obsid_list:
    pps_dir = wdir + "/" + obsid + "/pps"
    os.chdir(pps_dir)
    events_file = glob.glob("*PIEVLI0000.fits")[0]
    hdul = fits.open(events_file)

    RA_OBJ = float(hdul[0].header["RA_OBJ"])
    DEC_OBJ = float(hdul[0].header["DEC_OBJ"])
    RA_NOM = float(hdul[0].header["RA_NOM"])
    DEC_NOM = float(hdul[0].header["DEC_NOM"])

    RA_DIFF = RA_OBJ - RA_NOM
    DEC_DIFF = DEC_OBJ - DEC_NOM


    if RA_DIFF == 0.0 and DEC_DIFF == 0.0:
        #print(obsid)
        count+=1

    # print(obsid, RA_DIFF, DEC_DIFF)

    c_OBJ = SkyCoord(RA_OBJ, DEC_OBJ, unit='deg', frame='icrs')
    c_NOM = SkyCoord(RA_NOM, DEC_NOM, unit='deg', frame='icrs')
    sep = c_OBJ.separation(c_NOM) * 60 * u.arcmin / u.deg
    print(sep)

print(sep.unit)

# print(count)



# RA_OBJ  = 5.34016665000000E+01 / [deg] Ra of the observed object
# DEC_OBJ = -3.61402777000000E+01 / [deg] Dec of the observed object

# for row in header:
#     if "RA_NOM" in row:
#
#         print(row)
#     elif "DEC_NOM" in row:
#         print(row)

# RA_NOM  = 5.34016665000000E+01 / [deg] Ra of boresight
# DEC_NOM = -3.61402777000000E+01 / [deg] Dec of boresight