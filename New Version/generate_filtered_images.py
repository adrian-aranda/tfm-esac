import glob
import os
import logging
import shutil

import numpy as np

from commons import exec_task
from commons import sasinit
from commons import get_catalog
from commons import my_custom_logger

from astropy.io import fits
from datetime import datetime


def edetect_chain(odf_dir, pi):
    logger.info("TASK: edetect_chain")
    images_dir = odf_dir + "/images"
    os.chdir(images_dir)
    logger.info("Using:")
    #image_low = glob.glob("*_500_2000.fits")[0]
    image_low = glob.glob("*_500_2000_clean.fits")[0]
    logger.info("{}".format(image_low))
    #image_high = glob.glob("*_4500_10000.fits")[0]
    image_high = glob.glob("*_4500_10000_clean.fits")[0]
    logger.info("{}".format(image_high))
    #image_mid = glob.glob("*_2000_4500.fits")[0]
    image_mid = glob.glob("*_2000_4500_clean.fits")[0]
    logger.info("{}".format(image_high))
    clean_evts = glob.glob("{}/clean_*".format(odf_dir))[0]
    logger.info("{}".format(clean_evts))
    attitude_file = glob.glob("{}/atthk*".format(odf_dir))[0]
    logger.info("{}".format(attitude_file))
    ecf = 1  # Cuentas a flujo, nos da igual.
    task = f"edetect_chain imagesets={image_low} eventsets={clean_evts} " + \
           f"attitudeset={attitude_file} pimin={pi[0]} pimax={pi[1]} ecf={ecf} " + \
           "eboxl_list='pn_eboxlist_l_low.fits' eboxm_list='pn_eboxlist_m_low.fits' " + \
           "esp_nsplinenodes=16 eml_list='pn_emllist_low.fits' esen_mlmin=15 -V 5"
    status = exec_task(task)
    if (status != 0):
        print(f"Task \"{task}\" failed")
        raise Exception
    task = f"edetect_chain imagesets={image_high} eventsets={clean_evts} " + \
           f"attitudeset={attitude_file} pimin={pi[2]} pimax={pi[3]} ecf={ecf} " + \
           "eboxl_list='pn_eboxlist_l_high.fits' eboxm_list='pn_eboxlist_m_high.fits' " + \
           "esp_nsplinenodes=16 eml_list='pn_emllist_high.fits' esen_mlmin=15"
    status = exec_task(task)
    if (status != 0):
        logger.info("ERROR: Task edetect_chain failed. Check {}/tmp.log for more information".format(odf_dir))
        raise Exception
    task = f"edetect_chain imagesets={image_mid} eventsets={clean_evts} " + \
           f"attitudeset={attitude_file} pimin={pi[1]} pimax={pi[2]} ecf={ecf} " + \
           "eboxl_list='pn_eboxlist_l_low.fits' eboxm_list='pn_eboxlist_m_low.fits' " + \
           "esp_nsplinenodes=16 eml_list='pn_emllist_low.fits' esen_mlmin=15 -V 5"
    status = exec_task(task)
    if (status != 0):
        print(f"Task \"{task}\" failed")
        raise Exception
    logger.info("Sources detected correctly.")


def region(odf_dir):
    logger.info("TASK: region")
    os.chdir(odf_dir)
    bkg_file = glob.glob("bkg_*")
    if len(bkg_file) != 0:
        for bkg in bkg_file:
            os.remove(bkg)
    clean_evts = glob.glob("clean_*")[0]
    # Region for OBSMLI downloaded from te pipeline
    src_file = glob.glob("pps/*OBSMLI0000.fits")[0]
    task = f"region eventset={clean_evts} tempset=tempset.ds " + \
        f"srclisttab={src_file} operationstyle='global'"# radiusstyle='contour' outunit='xy' -V 5"

    # ## Region for the srclist from edetect_chain
    # src_file = glob.glob("{}/pn_emllist*".format(images_dir))[0]
    # task = f"region eventset={clean_evts} tempset=tempset.ds " + \
    #     f"srclisttab={src_file} operationstyle='global'"# radiusstyle='contour' outunit='xy' -V 5"

    logger.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if (status != 0):
        print (f"Task \"{task}\" failed")
        raise Exception
    logger.info("bkg file generated correctly.")


def ecoordconv(obsid):
    logger.info("TASK: ecoordconv")
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    RA = ""
    DEC = ""
    for row in data:
        if row[5] == obsid:
            RA = row[1]
            logger.info("COORDINATES: RA: {}".format(RA))
            DEC = row[2]
            logger.info("COORDINATES: DEC: {}".format(DEC))

    if RA == "" and DEC == "":
        logger.info("Coordinates not found in catalog.")
    images_dir = odf_dir + "/images"
    image_low = glob.glob("{}/*_500_2000.fits".format(images_dir))[0]
    coords = []

    task = f'ecoordconv imageset={image_low} x="{RA}" y="{DEC}" coordtype=eqpos'
    logger.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if (status != 0):
        print(f"Task \"{task}\" failed")
        raise Exception

    file = "tmp.log"
    with open(file, "r") as f:
        for line in f:
            if "X: Y:" in line:
                X = float(line.split(" ")[3])
                Y = float(line.split(" ")[4])
                coords.append([X, Y])

    print("X value is {}".format(X))
    print("Y value is {}".format(Y))
    logger.info("COORDINATES: X: {}".format(X))
    logger.info("COORDINATES: Y: {}".format(Y))

    # Delete the corresponding row in bkg_region.ds file.
    bkg_region = fits.open(f'bkg_region.ds', mode='update')
    data = bkg_region[1].data
    err = 50
    count = 0
    bad_row = None
    for row in data:
        if ((X - err) <= row[1][0] <= (X + err)) and ((Y - err) <= row[2][0] <= (Y + err)):
            bad_row = count
        count += 1

    if bad_row != None:
        data = np.delete(data, bad_row)  # !!!maybe repeated rows
    bkg_region[1].data = data
    bkg_region.writeto(f'bkg_region_clean.ds')
    logger.info("RA, DEC obtained correctly.\n\n")
    return [RA, DEC]


def filtered_region():
    logger.info("TASK: region")
    clean_evts = glob.glob("clean_*")[0]
    filtered_set = "filtered_{}".format(clean_evts)
    expr = f"region(bkg_region_clean.ds)"
    task = f'evselect table={clean_evts} filteredset={filtered_set} '+  \
        f'expression="{expr}"'
    logger.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if (status != 0):
        print (f"Task \"{task}\" failed")
        raise Exception
    logger.info("Image filtered with bkg_region_clean.ds generated correctly.")


def generate_filtered_images(odf_dir, bin_size, pi):
    logger.info("TASK: evselect")
    images_dir = odf_dir + "/images"
    os.chdir(images_dir)
    filtered = glob.glob("{}/filtered_*".format(odf_dir))[0]
    expr_high = f'PI in [{pi[2]}:{pi[3]}] &&  FLAG==0 && PATTERN in [0:4]'
    expr_mid = f'PI in [{pi[1]}:{pi[2]}] &&  FLAG==0 && PATTERN in [0:4]'
    expr_low = f'PI in [{pi[0]}:{pi[1]}] &&  FLAG==0 && PATTERN in [0:4]'

    task = f'evselect table={filtered} xcolumn=X ycolumn=Y imagebinning=binSize' + \
           f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
           f' expression=\'{expr_high}\'' + \
           f' withimageset=true imageset=image_filtered_high.fits'
    logger.info("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception

    task = f'evselect table={filtered} xcolumn=X ycolumn=Y imagebinning=binSize' + \
           f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
           f' expression=\'{expr_low}\'' + \
           f' withimageset=true imageset=image_filtered_low.fits'
    logger.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception

    task = f'evselect table={filtered} xcolumn=X ycolumn=Y imagebinning=binSize' + \
           f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
           f' expression=\'{expr_mid}\'' + \
           f' withimageset=true imageset=image_filtered_mid.fits'
    logger.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception
    os.chdir(odf_dir)
    logger.info("Images generated correctly.")


if __name__ == '__main__':

    # Initialize SAS
    sasinit()

    # obsid_list = ['0142270101', '0300480201', '0300480301', '0401060201', '0502630201', '0679380701', '0761500201',
    #               '0651360401', '0800732801', '0762870401', '0122520201', '0674330201', '0653040101', '0744412401',
    #               '0783881001', '0302580401', '0502430201', '0502430701', '0693010401', '0106060601', '0112550801',
    #               '0112551101', '0721890101', '0148250201', '0300140101', '0149880101', '0303930101', '0650380201',
    #               '0693741001', '0153170101', '0084140101', '0084140501', '0655343842', '0002970201', '0604210201',
    #               '0604210301', '0151490101', '0785110401', '0152900201', '0740820401', '0123100101', '0123100201',
    #               '0670040101', '0761112401', '0803240801', '0830190501', '0303820301', '0783520201', '0652810201',
    #               '0152460301', '0305750601', '0551750301', '0600920201', '0112830201', '0112830501', '0104860501',
    #               '0124900101', '0692510101', '0604830201', '0100240101', '0100240201', '0804272701', '0722140101',
    #               '0722140401', '0800270601', '0790380501', '0790380601', '0790380801', '0790381401', '0790381501',
    #               '0790380901', '0761100101', '0761100201', '0761100301', '0761100401', '0761101001', '0744640101',
    #               '0553561101', '0655346840', '0673000136', '0405380701', '0782350501']
    # Con Out of time events
    obsid_list = ['0721890101', '0084140101', '0084140501', '0604210201', '0604210301', '0152900201', '0123100201',
                  '0830190501', '0303820301', '0112830201', '0112830501', '0104860501', '0124900101', '0790380501',
                  '0790380601', '0790380801', '0790381401', '0790381501', '0790380901', '0761100101', '0761100201',
                  '0761100301', '0761100401', '0761101001']

    wdir = "/home/aaranda/tfm/obsid"

    bin_size = 80
    pi = [500, 2000, 4500, 10000]

    error_obsid = []


    count = 1
    for obsid in obsid_list:
        try:

            print("Executing {} of {}...".format(count, len(obsid_list)))
            count += 1
            odf_dir = "{}/{}".format(wdir, obsid)


            logfile = "{}/logs/rad_prof_{}.log".format(odf_dir, datetime.today().strftime('%Y%m%d-%H:%M'))
            logger = my_custom_logger(logfile)
            #logging.basicConfig(filename=logfile, filemode='w', level=logging.INFO, format='%(asctime)s - %(message)s')
            logger.info("OBSID: {} DATETIME: {}".format(obsid, datetime.today().strftime('%Y/%m/%d %H:%M')))
            logger.info("SAS_ODF={}".format(odf_dir))

            os.chdir(odf_dir)
            cif_file = "{}/ccf.cif".format(odf_dir)
            os.environ['SAS_CCF'] = cif_file
            SUM_SAS_file = glob.glob("*SUM.SAS")[0]
            os.environ['SAS_ODF'] = SUM_SAS_file

            # edetect_chain(odf_dir, images_dir, pi, logfile)

            print("Running step 1: region")
            region(odf_dir)
            print("Running step 2: ecoordconv")
            coords = ecoordconv(obsid)
            print("Running step 3: filtered region")
            filtered_region()
            print("Running step 4: evselect")
            generate_filtered_images(odf_dir, bin_size, pi)

        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass

    print(error_obsid)