import glob
import gzip
import os
import shutil
import tarfile

import requests

from sas_setup import sasinit
from sas_setup import exec_task
from astropy.io import fits


def build_dir(odf_dir):
    print("Checking directories...")
    if (not os.path.isdir(odf_dir)):
        os.mkdir(odf_dir)
        print("{} created".format(odf_dir))
    os.chdir(odf_dir)
    subfolders = ["gti", "images", "results", "pps", "logs"]
    for folder in subfolders:
        if (not os.path.isdir(folder)):
            os.mkdir(folder)
            print("{}/ created".format(folder))
    os.environ['SAS_ODF'] = odf_dir


def download_odf(obsid, odf_dir):
    os.chdir(odf_dir)
    manifest = glob.glob("MANIFEST*")  # Check if manifest exist, that is, odf was extracted.
    if len(manifest) == 0:
        nxsa_url = 'http://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno={}&level=ODF'.format(obsid)
        odf_tarfile = '{}/{}_odf.tar'.format(odf_dir, obsid)
        print('Downloading ODF for {} from NXSA...'.format(obsid))
        r = requests.get(nxsa_url)
        with open(odf_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print(".TAR file saved to {}".format(odf_tarfile))
        with tarfile.open(odf_tarfile, 'r') as tar:
            for member in tar.getmembers():
                f = tar.extract(member, path=odf_dir)
        tar = glob.glob("*.TAR")[0]
        print("Extracting .TAR file...")
        with tarfile.open(tar, 'r') as tar:
            for member in tar.getmembers():
                f = tar.extract(member, path=odf_dir)
        print(".TAR file extracted to {}".format(odf_tarfile))

        # Remove .tar files
        os.remove(odf_tarfile)
        tar = glob.glob("*.TAR")[0]
        os.remove(tar)
    else:
        print("ODF already downloaded in {}".format(odf_dir))


def download_pps(obsid, odf_dir):
    os.chdir(odf_dir)
    pps_files = glob.glob("pps/*.fits")

    if len(pps_files) == 0 or all("PIEVLI" not in s for s in pps_files):

        nxsa_url = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?' + \
                   'obsno={}&&instname=PN&extension=FTZ&level=PPS'.format(obsid)

        pps_tarfile = '{}/{}_pps.tar'.format(odf_dir, obsid)

        print(f'Downloading PPS products for {obsid} from NXSA...')
        r = requests.get(nxsa_url)
        with open(pps_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print('.TAR file saved to {}'.format(pps_tarfile))

        pps_dir = '{}/pps'.format(odf_dir)
        os.chdir(pps_dir)

        pattern = "PIEVLI"
        with tarfile.open(pps_tarfile, 'r') as tar:
            for member in tar.getmembers():
                if pattern in member.name:
                    f = tar.extract(member, path=wdir)
                    name = member.name.split('/')[2]  # obsid/tmp/file.tar
                    rename = name.split('.')[0] + '.fits.gz'
                    os.rename(name, rename)
                    with gzip.open(rename, 'rb') as f_in:
                        with open(rename.split('.gz')[0], 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    print('Extracted {} in {}'.format(rename.split('.gz')[0], wdir))
        os.remove(rename)
        os.chdir(odf_dir)
        os.remove(pps_tarfile)
    else:
        print("Events list already downloaded in {}/pps".format(odf_dir))


def download_source_lists(obsid, odf_dir):
    os.chdir(odf_dir)
    pps_files = glob.glob("pps/*.fits")

    if len(pps_files) == 0 or all("OBSMLI" not in s for s in pps_files):

        nxsa_url = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno={}&&name=OBSMLI&extension=FTZ&level=PPS'.format(
            obsid)
        pps_tarfile = '{}/{}_srclsts.tar'.format(odf_dir, obsid)
        print(f'Downloading OBSMLI products for {obsid} from NXSA...')
        r = requests.get(nxsa_url)
        with open(pps_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print('.TAR file saved to {}'.format(pps_tarfile))

        pps_dir = '{}/pps'.format(odf_dir)
        os.chdir(pps_dir)
        pattern = "EPX"
        with tarfile.open(pps_tarfile, 'r') as tar:
            for member in tar.getmembers():
                if pattern in member.name:
                    f = tar.extract(member, path=wdir)
                    name = member.name.split('/')[2]  # obsid/tmp/file.tar
                    rename = name.split('.')[0] + '.fits.gz'
                    os.rename(name, rename)
                    with gzip.open(rename, 'rb') as f_in:
                        with open(rename.split('.gz')[0], 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    print('Extracted {} in {}'.format(rename.split('.gz')[0], wdir))
        os.remove(rename)
        os.chdir(odf_dir)
        os.remove(pps_tarfile)
    else:
        print("Sources list already downloaded in {}/pps".format(odf_dir))


def cifbuild(odf_dir):
    os.chdir(odf_dir)
    cif_file = "{}/ccf.cif".format(odf_dir)
    if not os.path.isfile(cif_file):
        status = exec_task("cifbuild")
        if (status != 0):
            raise Exception
        print("{} generated correctly.".format(cif_file))
        os.environ['SAS_CCF'] = cif_file
        print("SAS_CCF={}".format(cif_file))
    else:
        print("cif.ccf already exists.")
        os.environ['SAS_CCF'] = cif_file
        print("SAS_CCF={}".format(cif_file))


def odfingest(odf_dir):
    os.chdir(odf_dir)
    SUM_SAS_file = glob.glob("*SUM.SAS")
    if len(SUM_SAS_file) == 0:
        status = exec_task("odfingest")
        if (status != 0):
            print(f"Task odfingest failed")
            #raise Exception
        SUM_SAS_file = glob.glob("*SUM.SAS")[0]
        os.environ['SAS_ODF'] = SUM_SAS_file
        print("SAS_ODF={}".format(SUM_SAS_file))
    else:
        print("*SUM.SAS file already exists.")


if __name__ == '__main__':
    sas_dir = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155"
    sasinit(sas_dir=sas_dir)
    os.environ['SAS_CCFPATH'] = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155/calibration"

    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    obsid_list = []
    for row in data:
        obsid_list.append(row[5])

    wdir = "/home/aaranda/tfm/obsid"

    error_obsid = []
    for obsid in obsid_list:
        try:
            odf_dir = "{}/{}".format(wdir, obsid)
            build_dir(odf_dir)

            download_odf(obsid, odf_dir)
            download_pps(obsid, odf_dir)
            download_source_lists(obsid, odf_dir)

            cifbuild(odf_dir)
            odfingest(odf_dir)

        except:
            error_obsid.append(obsid)
            print("Error ocurred with obsid: {}".format(obsid))
            pass
    print(error_obsid)
