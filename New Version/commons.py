import logging
import os
import subprocess
import sys
from astropy.io import fits

def sasinit():
    sas_dir = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155"
    os.environ["SAS_DIR"] = sas_dir
    os.environ["SAS_PATH"] = os.environ["SAS_DIR"]
    os.environ["SAS_VERBOSITY"] = "4"
    os.environ["SAS_SUPPRESS_WARNING"] = "1"
    path = os.environ["PATH"]
    os.environ["PATH"] = f"{sas_dir}/bin:{sas_dir}/binextra:{path}"
    if "LD_LIBRARY_PATH" in os.environ.keys():
        ld_path = os.environ["LD_LIBRARY_PATH"]
    # lib_path = f"{sas_dir}/lib:{sas_dir}/libextra:{sas_dir}/libsys:{ld_path}"
    lib_path = f"{sas_dir}/lib:{sas_dir}/libextra:{sas_dir}"
    os.environ["LD_LIBRARY_PATH"] = lib_path
    os.environ["PERL5LIB"] = "{}/lib/perl5".format(sas_dir)
    os.environ['SAS_CCFPATH'] = "/home/aaranda/SAS/sas_18.0.0-Ubuntu16.04-64/xmmsas_20190531_1155/calibration"
    # sasversion
    # perl -e "print qq(@INC)"


def exec_task(task, verbose=True):
    try:
        # Write the shell output to tmp.log file.
        fout = open("tmp.log", "w")
        result = subprocess.run(task, shell=True, stdout=fout, stderr=subprocess.STDOUT)
        retcode = result.returncode
        fout.close()
        if retcode < 0:
            if (verbose):
                print(f"Execution of {task} was terminated by code {-retcode}.", file=sys.stderr)
        else:
            if (verbose):
                print(f"Execution of {task} returned {retcode}.", file=sys.stderr)
    except OSError as e:
        print(f"Execution of {task} failed:", e, file=sys.stderr)
    return retcode

def get_catalog():
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_TFM_Adrian.fits')
    data = bll_catalog[1].data
    obsid_list = []
    for row in data:
        obsid_list.append(row[4])
    return obsid_list

def get_outoftime_evts():
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_TFM_Adrian.fits')
    data = bll_catalog[1].data
    OutOfTime_list = []
    for row in data:
        if row[8] == 'SI':
            OutOfTime_list.append(row[4])
    return OutOfTime_list

def my_custom_logger(logger_name, level=logging.INFO):
    """
    Method to return a custom logger with the given name and level
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    format_string = '%(asctime)s - %(message)s'
    log_format = logging.Formatter(format_string)
    file_handler = logging.FileHandler(logger_name, mode='a')
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    return logger