from datetime import datetime
import logging
import os

from sas_setup import exec_task
from sas_setup import sasinit
from sas_setup import get_catalog

import glob


def radial_prof_psf(eq_coords, logfile):
    log = open(logfile, "a")
    log.write("TASK: eradial\n")

    image = glob.glob("psf.fits")[0]

    # Find circle values on ds9:
    # !!! No coger valores de radio inferiores a 400
    # ------------------------------------------------------------------

    r = 2.0 / 60.
    circle = "{},{},{}".format(eq_coords[0], eq_coords[1], r)
    log.write("CIRCLE: {}\n".format(circle))
    # ------------------------------------------------------------------

    task = f"eradial imageset={image} srcexp='(RA,DEC) in CIRCLE({circle})' psfenergy=1.0 centroid='yes' binwidth=6.0"
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception
    os.rename("radprof.ds", f"radprof_psf.ds")

    log.write("Theorical PSF radial profile generated correctly.\n\n")
    log.close()

def detmask(odf_dir, pi):
    logging.info("TASK: atthkgen")
    task = "atthkgen"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    logging.info("atthkegn generated correctly.")
    logging.info("TASK: atthkgen")
    image_low = "{}/images/image_filtered_low.fits".format(odf_dir)
    image_high = "{}/images/image_filtered_high.fits".format(odf_dir)
    atthk = glob.glob("atthk.dat")[0]
    evlist = glob.glob("filtered_clean_*")[0]
    expfile_low = "expfile_low.fits"
    expfile_high = "expfile_high.fits"
    task = f'eexpmap imageset={image_low} attitudeset={atthk} eventset={evlist} ' + \
           f'expimageset={expfile_low} pimin={pi[0]} pimax={pi[1]}'
    status = exec_task(task)
    if (status != 0):
        raise Exception
    task = f'eexpmap imageset={image_high} attitudeset={atthk} eventset={evlist} ' + \
           f'expimageset={expfile_high} pimin={pi[2]} pimax={pi[3]}'
    status = exec_task(task)
    if (status != 0):
        raise Exception
    logging.info("expfiles generated correctly.")

    detfile_low = "detfile_low.fits"
    detfile_high = "detfile_high.fits"
    task = f"emask expimageset={expfile_low} detmaskset={detfile_low} threshold1=0.3 threshold2=0.5 withregionset=true regionset=bkg_region_clean.ds"
    #task = f"emask expimageset={expfile_low} detmaskset={detfile_low} threshold1=0.3 threshold2=0.5"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    task = f"emask expimageset={expfile_high} detmaskset={detfile_high} threshold1=0.3 threshold2=0.5 withregionset=true regionset=bkg_region_clean.ds"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    # task = f"emask expimageset=psf.fits detmaskset={detfile_high} regionset='bkg_region_clean.ds' threshold1=0.3 threshold2=0.5"
    # status = exec_task(task)
    # if (status != 0):
    #     raise Exception
    logging.info("detfiles generated correctly.")

def psf_gen(coords):
    images_dir = ""
    image_low = glob.glob("{}/image_filtered_low*".format(images_dir))[0]
    task = f"psfgen image={image_low} energy=1000 level=ELLBETA coordtype=EQPOS x={coords[0]} y={coords[1]} xsize=400 ysize=400 output=psf.fits"
    status = exec_task(task)
    if (status != 0):
        raise Exception

def cal_view():
    task = "calview"
    status = exec_task(task)
    if (status != 0):
        raise Exception


if __name__ == '__main__':

    # Initialize SAS
    sasinit()

    # Get catalog obsid list
    obsid_list = get_catalog()

    wdir = "/home/aaranda/tfm/obsid"

    bin_size = 80
    pi = [500, 2000, 4500, 10000]

    error_obsid = []

    obsid_list = ["0692840501", "0165770201", "0600920201", "0551750301", "0727770901",
            "0310190101", "0094383101", "0804272801", "0673000136", "0041180801"]

    count = 1
    for obsid in obsid_list:
        # try:

            print("Executing {} of {}...".format(count, len(obsid_list)))
            count += 1
            odf_dir = "{}/{}".format(wdir, obsid)

            logfile = "{}/logs/phot_{}.log".format(odf_dir, datetime.today().strftime('%Y%m%d-%H:%M'))
            logging.basicConfig(filename=logfile, filemode='w', level=logging.INFO, format='%(asctime)s - %(message)s')
            logging.info("OBSID: {} DATETIME: {}".format(obsid, datetime.today().strftime('%Y/%m/%d %H:%M')))
            logging.info("SAS_ODF={}".format(odf_dir))

            os.chdir(odf_dir)
            cif_file = "{}/ccf.cif".format(odf_dir)
            os.environ['SAS_CCF'] = cif_file
            SUM_SAS_file = glob.glob("*SUM.SAS")[0]
            os.environ['SAS_ODF'] = SUM_SAS_file

            detmask(odf_dir, pi)
            #
            # psf_gen(coords)
            # radial_prof_psf(coords, logfile)

            # cal_view()


        # except:
        #     error_obsid.append(obsid)
        #     print("Error ocurred with obsid: {}".format(obsid))
        #     pass

    print(error_obsid)