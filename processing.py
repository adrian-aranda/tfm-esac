import glob
import os

import numpy as np
from datetime import datetime
from astropy.io import fits

from sas_setup import exec_task
from sas_setup import  sasinit

def evselect(odf_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: evselect\n")
    os.chdir("{}/pps".format(odf_dir))
    evlist = glob.glob("*PIEVLI0000.fits")[0]
    log.write("EVENTS LIST: {}\n".format(evlist))
    # the exposure
    expo = evlist.split('PIEVLI0000.fits')[0]
    rate = "{}/rate_{}.fits".format(odf_dir, expo)
    log.write("RATE: {}\n".format(rate))
    expr = '#XMMEA_EP && (PI>10000&&PI<12000) && (PATTERN==0)'
    task = f'evselect table={evlist} withrateset=Y rateset={rate}' + \
    ' maketimecolumn=Y timebinsize=100 makeratecolumn=Y' + \
    f' expression=\'{expr}\''
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        log.write("ERROR: Task evselect failed. Check {}/tmp.log for more information\n".format(odf_dir))
        raise Exception
    log.write("rate file generated correctly.\n\n")
    log.close()

def tabgtigen(odf_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: tabgtigen\n")
    gti_dir = "{}/gti".format(odf_dir)
    rate = glob.glob("{}/rate_*".format(odf_dir))[0]
    os.chdir(gti_dir)
    if (len(rate) == 0):
        log.write("No rate file found in {}\n".format(odf_dir))
    else:
        log.write("Found {} calibrated events list.\n".format(rate))
    log.write("Generating Good Time Intervals for {}...\n".format(rate))
    expo = rate.split('rate')[1]
    gti = 'gti{}'.format(expo)
    log.write("GTI: {}\n".format(gti))
    expr = 'RATE<=0.4'
    task = f'tabgtigen table="{rate}" gtiset={gti}' + \
    f' expression=\'{expr}\''
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        log.write("ERROR: Task tabgtigen failed. Check {}/tmp.log for more information\n".format(odf_dir))
        raise Exception
    os.chdir(odf_dir)
    return gti_dir
    log.write("{} generated correctly.\n\n".format(gti))
    log.close()

def evselect_clean(odf_dir, gti_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: evselect\n")
    os.chdir("{}/pps".format(odf_dir))
    evlist = glob.glob("*PIEVLI0000.fits")[0]
    gti = glob.glob("{}/gti_*".format(gti_dir))[0]
    expo = evlist.split('PIEVLI0000.fits')[0]
    log.write("Using PI>150 for evselect.\n".format(gti))
    expr = f"#XMMEA_EP && gti({gti},TIME) && (PI>150)"
    task = f'evselect table={evlist} withfilteredset=Y ' + \
    f'filteredset={odf_dir}/clean_{expo}.fits ' +  \
    f'destruct=Y keepfilteroutput=T expression=\'{expr}\''
    log.write("Filtering {} with GTI...\n".format(expo))
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        log.write("ERROR: Task evselect failed. Check {}/tmp.log for more information\n".format(odf_dir))
        raise Exception
    log.write("clean file generated correctly.\n\n")
    log.close()
    os.chdir(odf_dir)


def generate_images(odf_dir, bin_size, pi, logfile):
    log = open(logfile, "a")
    log.write("TASK: evselect\n")
    log.write("ENERGY BAND 1: {} - {} eV\n".format(pi[0], pi[1]))
    log.write("ENERGY BAND 2: {} - {} eV\n".format(pi[2], pi[3]))
    log.write("BIN SIZE: {}\n".format(bin_size))
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
        task = f'evselect table={clean_file} xcolumn=X ycolumn=Y imagebinning=binSize' +  \
             f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
             f' expression=\'{expr[i]}\'' +  \
             f' withimageset=true imageset={image_name[i]}'
        log.write("COMMAND: {}\n".format(task))
        status = exec_task(task)
        if (status != 0):
            log.write("ERROR: Task evselect failed. Check {}/tmp.log for more information\n".format(odf_dir))
            raise Exception
        log.write("Image {} generated.\n".format(image_name[i]))
    log.write("Images generated correctly.\n\n")
    log.close()
    return images_dir


def region(odf_dir, images_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: region\n")
    os.chdir(odf_dir)
    bkg_file = glob.glob("bkg_*")
    if len(bkg_file) != 0:
        for bkg in bkg_file:
            os.remove(bkg)
    clean_evts = glob.glob("clean_*")[0]
    src_file = glob.glob("pps/*OBSMLI0000.fits".format(images_dir))[0]
    task = f"region eventset={clean_evts} tempset=tempset.ds " + \
        f"srclisttab={src_file} operationstyle='global'"# radiusstyle='contour'"
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        print (f"Task \"{task}\" failed")
        raise Exception
    log.write("bkg file generated correctly.\n\n")
    log.close()


def ecoordconv(obsid, images_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: ecoordconv\n")
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    RA = ""
    DEC = ""
    for row in data:
        if row[5] == obsid:
            RA = row[1]
            log.write("COORDINATES: RA: {}\n".format(RA))
            DEC = row[2]
            log.write("COORDINATES: DEC: {}\n".format(DEC))

    if RA == "" and DEC == "":
        log.write("Coordinates not found in catalog.\n")
    image_low = glob.glob("{}/*_500_2000.fits".format(images_dir))[0]
    coords = []

    task = f'ecoordconv imageset={image_low} x="{RA}" y="{DEC}" coordtype=eqpos'
    log.write("COMMAND: {}\n".format(task))
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
    log.write("COORDINATES: X: {}\n".format(X))
    log.write("COORDINATES: Y: {}\n".format(Y))

    # Delete the corresponding row in bkg_region.ds file.
    bkg_region = fits.open(f'bkg_region.ds', mode='update')
    data = bkg_region[1].data
    err = 50
    count = 0
    for row in data:
        if ((X - err) <= row[1][0] <= (X + err)) and ((Y - err) <= row[2][0] <= (Y + err)):
            bad_row = count
        count += 1

    data = np.delete(data, bad_row)  # !!!maybe repeated rows
    bkg_region[1].data = data
    bkg_region.writeto(f'bkg_region_clean.ds')
    log.write("RA, DEC obtained correctly.\n\n")
    log.close()
    return [RA, DEC]


def filtered_region(logfile):
    log = open(logfile, "a")
    log.write("TASK: region\n")
    clean_evts = glob.glob("clean_*")[0]
    filtered_set = "filtered_{}".format(clean_evts)
    expr = f"region(bkg_region_clean.ds)"
    task = f'evselect table={clean_evts} filteredset={filtered_set} '+  \
        f'expression="{expr}"'
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        print (f"Task \"{task}\" failed")
        raise Exception
    log.write("Image filtered with bkg_region_clean.ds generated correctly.\n\n")
    log.close()


def generate_filtered_images(odf_dir, images_dir, bin_size, pi, logfile):
    log = open(logfile, "a")
    log.write("TASK: evselect\n")
    os.chdir(images_dir)
    filtered = glob.glob("{}/filtered_*".format(odf_dir))[0]
    expr_high = f'PI in [{pi[2]}:{pi[3]}] &&  FLAG==0 && PATTERN in [0:4]'
    expr_low = f'PI in [{pi[0]}:{pi[1]}] &&  FLAG==0 && PATTERN in [0:4]'

    print(f"*** Generating images...")

    task = f'evselect table={filtered} xcolumn=X ycolumn=Y imagebinning=binSize' + \
           f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
           f' expression=\'{expr_high}\'' + \
           f' withimageset=true imageset=image_filtered_high.fits'
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception

    task = f'evselect table={filtered} xcolumn=X ycolumn=Y imagebinning=binSize' + \
           f' ximagebinsize={bin_size} yimagebinsize={bin_size}' + \
           f' expression=\'{expr_low}\'' + \
           f' withimageset=true imageset=image_filtered_low.fits'
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception
    os.chdir(odf_dir)
    log.write("Images generated correctly.\n\n")
    log.close()


def radial_prof(eq_coords, images_dir, logfile):
    log = open(logfile, "a")
    log.write("TASK: eradial\n")

    image_low = glob.glob("{}/image_filtered_low*".format(images_dir))[0]
    image_high = glob.glob("{}/image_filtered_high*".format(images_dir))[0]

    # Find circle values on ds9:
    # !!! No coger valores de radio inferiores a 400
    # ------------------------------------------------------------------

    r = 2.0 / 60.
    circle = "{},{},{}".format(eq_coords[0], eq_coords[1], r)
    log.write("CIRCLE: {}\n".format(circle))
    # ------------------------------------------------------------------

    task = f"eradial imageset={image_low} srcexp='(RA,DEC) in CIRCLE({circle})' psfenergy=1.0"
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception
    os.rename("radprof.ds", f"radprof_low.ds")

    task = f"eradial imageset={image_high} srcexp='(RA,DEC) in CIRCLE({circle})' psfenergy=5.0 centroid='yes' binwidth=6.0"  # binwidth = 4.0 or 6.0
    log.write("COMMAND: {}\n".format(task))
    status = exec_task(task)
    if (status != 0):
        raise Exception
    os.rename("radprof.ds", f"radprof_high.ds")
    log.write("Radial profiles generated correctly.\n\n")
    log.close()

def detmask(odf_dir, pi, logfile):
    log = open(logfile, "a")
    log.write("TASK: atthkgen\n")
    task = "atthkgen"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    log.write("atthkegn generated correctly.\n\n")
    log.write("TASK: atthkgen\n")
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
    log.write("expfiles generated correctly.\n\n")

    detfile_low = "detfile_low.fits"
    detfile_high = "detfile_high.fits"
    task = f"emask expimageset={expfile_low} detmaskset={detfile_low} threshold1=0.3 threshold2=0.5"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    task = f"emask expimageset={expfile_high} detmaskset={detfile_high} threshold1=0.3 threshold2=0.5"
    status = exec_task(task)
    if (status != 0):
        raise Exception
    log.write("detfiles generated correctly.\n\n")
    log.close()


if __name__=='__main__':
    sas_dir = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155"
    sasinit(sas_dir=sas_dir)
    os.environ['SAS_CCFPATH'] = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155/calibration"

    obsid_list = ["0651360401", "0305800501", "0723802201", "0800732801", "0762870401", "0100241001", "0782350501",
                  "0405380701", "0673000136", "0655346840"]

    wdir = "/home/aaranda/tfm/obsid"

    bin_size = 80
    pi = [500, 2000, 4500, 10000]

    error_obsid = []
    test = ["0651360401"]


    test_list = ["0651360401", "0305800501", "0723802201", "0800732801", "0762870401", "0100241001", "0782350501", "0405380701", "0673000136", "0655346840"]
    for obsid in test_list:

        try:
            odf_dir = "{}/{}".format(wdir, obsid)
            logfile = "{}/logs/{}_{}.log".format(odf_dir, obsid, datetime.today().strftime('%Y%m%d:%H:%M:%S'))
            log = open(logfile, "w")
            log.write("=====================================================\n")
            log.write("||                                                 ||\n")
            log.write("|| OBSID: {} DATETIME: {} ||\n".format(obsid, datetime.today().strftime('%Y/%m/%d %H:%M:%S')))
            log.write("||                                                 ||\n")
            log.write("=====================================================\n")
            log.write("\nSAS_ODF={}\n\n".format(odf_dir))
            log.close()

            os.chdir(odf_dir)
            cif_file = "{}/ccf.cif".format(odf_dir)
            os.environ['SAS_CCF'] = cif_file
            SUM_SAS_file = glob.glob("*SUM.SAS")[0]
            os.environ['SAS_ODF'] = SUM_SAS_file

            evselect(odf_dir, logfile)
            gti_dir = tabgtigen(odf_dir, logfile)
            evselect_clean(odf_dir, gti_dir, logfile)
            images_dir = generate_images(odf_dir, bin_size, pi, logfile)
            region(odf_dir, images_dir, logfile)
            coords = ecoordconv(obsid, images_dir, logfile)
            filtered_region(logfile)
            generate_filtered_images(odf_dir, images_dir, bin_size, pi, logfile)
            radial_prof(coords, images_dir, logfile)
            detmask(odf_dir, pi, logfile)

        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass
    print(error_obsid)