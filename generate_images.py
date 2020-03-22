import glob
import os
import logging

from datetime import datetime

from sas_setup import exec_task
from sas_setup import sasinit
from sas_setup import get_catalog


def evselect(odf_dir):
    logging.info("TASK: evselect")
    os.chdir("{}/pps".format(odf_dir))
    evlist = glob.glob("*PIEVLI0000.fits")[0]
    logging.info("EVENTS LIST: {}".format(evlist))
    expo = evlist.split('PIEVLI0000.fits')[0]
    rate = "{}/rate_{}.fits".format(odf_dir, expo)
    logging.info("RATE: {}".format(rate))
    expr = '#XMMEA_EP && (PI>10000&&PI<12000) && (PATTERN==0)'
    task = f'evselect table={evlist} withrateset=Y rateset={rate}' + \
           ' maketimecolumn=Y timebinsize=100 makeratecolumn=Y' + \
           f' expression=\'{expr}\''
    logging.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if status != 0:
        logging.info("ERROR: Task evselect failed. Check {}/tmp.log for more information".format(odf_dir))
        raise Exception
    logging.info("rate file generated correctly.")


def tabgtigen(odf_dir):
    logging.info("TASK: tabgtigen")
    gti_dir = "{}/gti".format(odf_dir)
    rate = glob.glob("{}/rate_*".format(odf_dir))[0]
    os.chdir(gti_dir)
    if (len(rate) == 0):
        logging.info("No rate file found in {}".format(odf_dir))
    else:
        logging.info("Found {} calibrated events list.".format(rate))
    logging.info("Generating Good Time Intervals for {}...".format(rate))
    expo = rate.split('rate')[1]
    gti = 'gti{}'.format(expo)
    logging.info("GTI: {}".format(gti))
    expr = 'RATE<=0.4'
    task = f'tabgtigen table="{rate}" gtiset={gti}' + \
           f' expression=\'{expr}\''
    logging.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if status != 0:
        logging.info("ERROR: Task tabgtigen failed. Check {}/tmp.log for more information".format(odf_dir))
        raise Exception
    os.chdir(odf_dir)
    logging.info("{} generated correctly.".format(gti))
    return gti_dir


def evselect_clean(odf_dir, gti_dir):
    logging.info("TASK: evselect")
    os.chdir("{}/pps".format(odf_dir))
    evlist = glob.glob("*PIEVLI0000.fits")[0]
    gti = glob.glob("{}/gti_*".format(gti_dir))[0]
    expo = evlist.split('PIEVLI0000.fits')[0]
    logging.info("Using PI>150 for evselect.".format(gti))
    expr = f"#XMMEA_EP && gti({gti},TIME) && (PI>150)"
    task = f'evselect table={evlist} withfilteredset=Y ' + \
           f'filteredset={odf_dir}/clean_{expo}.fits ' + \
           f'destruct=Y keepfilteroutput=T expression=\'{expr}\''
    logging.info("Filtering {} with GTI...".format(expo))
    logging.info("COMMAND: {}".format(task))
    status = exec_task(task)
    if status != 0:
        logging.info("ERROR: Task evselect failed. Check {}/tmp.log for more information".format(odf_dir))
        raise Exception
    logging.info("clean file generated correctly.")
    os.chdir(odf_dir)


def generate_images(odf_dir, bin_size, pi):
    logging.info("TASK: evselect")
    logging.info("ENERGY BAND 1: {} - {} eV".format(pi[0], pi[1]))
    logging.info("ENERGY BAND 2: {} - {} eV".format(pi[2], pi[3]))
    logging.info("BIN SIZE: {}".format(bin_size))
    os.chdir("{}/pps".format(odf_dir))
    evlist = glob.glob("*PIEVLI0000.fits")[0]
    expo = evlist.split('PIEVLI0000.fits')[0]
    clean_file = glob.glob("{}/clean_*".format(odf_dir))[0]
    images_dir = "{}/images".format(odf_dir)
    os.chdir(images_dir)
    image_name = [f'image_{expo}_{pi[0]}_{pi[1]}.fits',
                  f'image_{expo}_{pi[2]}_{pi[3]}.fits']
    expr = [f'PI in [{pi[0]}:{pi[1]}] &&  FLAG==0 && PATTERN in [0:4]',
            f'PI in [{pi[2]}:{pi[3]}] &&  FLAG==0 && PATTERN in [0:4]']
    for i in range(len(expr)):
        task = f'evselect table={clean_file} xcolumn=X ycolumn=Y imagebinning=binSize' + \
               f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
               f' expression=\'{expr[i]}\'' + \
               f' withimageset=true imageset={image_name[i]}'
        logging.info("COMMAND: {}\n".format(task))
        status = exec_task(task)
        if status != 0:
            logging.info("ERROR: Task evselect failed. Check {}/tmp.log for more information".format(odf_dir))
            raise Exception
        logging.info("Image {} generated.".format(image_name[i]))
    logging.info("Images generated correctly.")


if __name__ == '__main__':

    # Initialize SAS
    sasinit()

    # Get catalog obsid list
    obsid_lits = get_catalog()

    wdir = "/home/aaranda/tfm/obsid"


    bin_size = 80
    pi = [500, 2000, 4500, 10000]

    error_obsid = []

    test = ["0692840501", "0165770201", "0600920201", "0551750301", "0727770901",
            "0761112401", "0094383101",  "0804272801", "0086750101", "0041180801"]

    for obsid in test:
        try:

            odf_dir = "{}/{}".format(wdir, obsid)

            logfile = "{}/logs/gen_imgs_{}.log".format(odf_dir, datetime.today().strftime('%Y%m%d-%H:%M'))
            logging.basicConfig(filename=logfile, filemode='w', level=logging.INFO, format='%(asctime)s - %(message)s')
            logging.info("OBSID: {} DATETIME: {}".format(obsid, datetime.today().strftime('%Y/%m/%d %H:%M')))
            logging.info("SAS_ODF={}".format(odf_dir))

            os.chdir(odf_dir)
            cif_file = "{}/ccf.cif".format(odf_dir)
            os.environ['SAS_CCF'] = cif_file
            SUM_SAS_file = glob.glob("*SUM.SAS")[0]
            os.environ['SAS_ODF'] = SUM_SAS_file


            evselect(odf_dir)
            gti_dir = tabgtigen(odf_dir)
            evselect_clean(odf_dir, gti_dir)
            generate_images(odf_dir, bin_size, pi)


        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass

    print(error_obsid)
