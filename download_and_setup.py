#!/usr/bin/env python
# coding: utf-8

# # MODULES

# In[1]:


import os
import requests
import tarfile
import gzip
import shutil
import subprocess
import sys
import glob
from multiprocessing import Process


# # INITIALIZE SAS

# In[2]:


sas_dir = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155"
os.environ["SAS_DIR"]= sas_dir
os.environ["SAS_PATH"]=os.environ["SAS_DIR"]
os.environ["SAS_VERBOSITY"]="4"
os.environ["SAS_SUPPRESS_WARNING"]="1"
path = os.environ["PATH"]
os.environ["PATH"] = f"{sas_dir}/bin:{sas_dir}/binextra:{path}"
ld_path = os.environ["LD_LIBRARY_PATH"]
lib_path = f"{sas_dir}/lib:{sas_dir}/libextra:{sas_dir}/libsys:{ld_path}"
os.environ["LD_LIBRARY_PATH"] = lib_path
os.environ["PERL5LIB"] = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155/lib/perl5"
get_ipython().system('sasversion')
get_ipython().system('perl -e "print qq(@INC)"')


# # FUNCTIONS

# In[3]:


def exec_task(task, verbose = True):
    try:
        # Write the shell output to tmp.log file.
        fout = open("tmp.log", "w")
        result = subprocess.run(task, shell = True, stdout = fout, stderr = subprocess.STDOUT)
        retcode = result.returncode
        fout.close()
        if retcode < 0:
            if (verbose):
                print(f"Execution of {task} was terminated by code {-retcode}.", file = sys.stderr)
        else:
            if (verbose):
                print(f"Execution of {task} returned {retcode}.", file = sys.stderr)
    except OSError as e:
        print(f"Execution of {task} failed:", e, file = sys.stderr)
    return retcode


# In[4]:


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


# In[5]:


def download_odf(obsid, odf_dir):

    os.chdir(odf_dir)
    manifest = glob.glob("MANIFEST*") # Check if manifest exist, that is, odf was extracted.
    if len(manifest) == 0:
        nxsa_url = 'http://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno={}&level=ODF'.format(obsid)
        odf_tarfile = '{}/{}_odf.tar'.format(odf_dir, obsid)
        print('Downloading ODF for {} from NXSA...'.format(obsid))
        r = requests.get(nxsa_url)
        with open(odf_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print(".TAR file saved to {}".format(odf_tarfile))
        with tarfile.open(odf_tarfile,'r') as tar:
            for member in tar.getmembers():
                    f = tar.extract(member, path = odf_dir)
        tar = glob.glob("*.TAR")[0]
        print("Extracting .TAR file...")
        with tarfile.open(tar, 'r') as tar:
            for member in tar.getmembers():
                f = tar.extract(member, path = odf_dir)
        print(".TAR file extracted to {}".format(odf_tarfile))
        
        # Remove .tar files
        os.remove(odf_tarfile)
        tar = glob.glob("*.TAR")[0]
        os.remove(tar)
    else:
        print("ODF already downloaded in {}".format(odf_dir))


# In[6]:


def download_pps(obsid, odf_dir):
    
    os.chdir(odf_dir)
    pps_files = glob.glob("pps/*.fits")
    
    if len(pps_files) == 0 or all("PIEVLI" not in s for s in pps_files):
        
        nxsa_url = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?' +                     'obsno={}&&instname=PN&extension=FTZ&level=PPS'.format(obsid)

        pps_tarfile = '{}/{}_pps.tar'.format(odf_dir, obsid)

    
        print (f'Downloading PPS products for {obsid} from NXSA...')
        r = requests.get(nxsa_url)
        with open(pps_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print('.TAR file saved to {}'.format(pps_tarfile))

        pps_dir = '{}/pps'.format(odf_dir)
        os.chdir(pps_dir)

        pattern = "PIEVLI"
        with tarfile.open(pps_tarfile,'r') as tar:
            for member in tar.getmembers():
                if pattern in member.name:
                    f = tar.extract(member,path = wdir)
                    name = member.name.split('/')[2] #obsid/tmp/file.tar
                    rename = name.split('.')[0] + '.fits.gz'
                    os.rename(name, rename)
                    with gzip.open(rename, 'rb') as f_in:
                        with open(rename.split('.gz')[0], 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    print ('Extracted {} in {}'.format(rename.split('.gz')[0], wdir))
        os.remove(rename)
        os.chdir(odf_dir)
        os.remove(pps_tarfile)
    else:
        print("Events list already downloaded in {}/pps".format(odf_dir))


# In[7]:


def download_source_lists(obsid, odf_dir):

    os.chdir(odf_dir)
    pps_files = glob.glob("pps/*.fits")
    
    if len(pps_files) == 0 or all("OBSMLI" not in s for s in pps_files):
        
        nxsa_url = 'https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno={}&&name=OBSMLI&extension=FTZ&level=PPS'.format(obsid)
        pps_tarfile = '{}/{}_srclsts.tar'.format(odf_dir, obsid)
        print (f'Downloading OBSMLI products for {obsid} from NXSA...')
        r = requests.get(nxsa_url)
        with open(pps_tarfile, "wb") as tmp:
            tmp.write(r.content)
        print('.TAR file saved to {}'.format(pps_tarfile))

        pps_dir = '{}/pps'.format(odf_dir)
        os.chdir(pps_dir)
        pattern = "EPX"
        with tarfile.open(pps_tarfile,'r') as tar:
            for member in tar.getmembers():
                if pattern in member.name:
                        f=tar.extract(member,path=wdir)
                        name = member.name.split('/')[2] #obsid/tmp/file.tar
                        rename = name.split('.')[0] + '.fits.gz'
                        os.rename(name, rename)
                        with gzip.open(rename, 'rb') as f_in:
                            with open(rename.split('.gz')[0], 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        print ('Extracted {} in {}'.format(rename.split('.gz')[0], wdir))
        os.remove(rename)
        os.chdir(odf_dir)
        os.remove(pps_tarfile)
    else:
        print("Sources list already downloaded in {}/pps".format(odf_dir))


# In[8]:


def cifbuild(odf_dir):
    os.chdir(odf_dir)
    if not os.path.isfile("ccf.cif"):
        status = exec_task("cifbuild")
        if (status != 0):
            log.write("ERROR: Task cifbuild failed. Check {}/tmp.log for more information\n".format(odf_dir))
            raise Exception
        cif_file = "{}/ccf.cif".format(odf_dir)
        print("{} generated correctly.".format(cif_file))
        os.environ['SAS_CCF'] = cif_file
        print("SAS_CCF={}".format(cif_file))
    else:
        print("cif.ccf already exists.")


# In[9]:


def odfingest(odf_dir):
    os.chdir(odf_dir)
    SUM_SAS_file = glob.glob("*SUM.SAS")
    if len(SUM_SAS_file) == 0:
        status = exec_task("odfingest")
        if (status != 0):
            print (f"Task odfingest failed")
            raise Exception
        SUM_SAS_file = glob.glob("*SUM.SAS")[0]
        os.environ['SAS_ODF'] = SUM_SAS_file
        print("SAS_ODF={}".format(SUM_SAS_file))
    else:
        print("*SUM.SAS file already exists.")


# In[11]:


obsid_list = ["0651360401", "0305800501", "0723802201", "0800732801", "0762870401", "0100241001", "0782350501", "0405380701", "0673000136", "0655346840"]

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

