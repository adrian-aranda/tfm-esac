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
    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    obsid_list = []
    for row in data:
        if row[10] != "PrimeSmallWindow":
            obsid_list.append(row[5])
    return obsid_list

def get_catalog_v2():
    bl_lacs = ['PKS0548-322', 'OJ287', 'XMMJ12484+0830', 'B30045+395', 'RXSJ01535-0118', 'XMMJ03114-7701',
               '1WGAJ0428.8-3805', 'RXSJ07514+1730', '1WGAJ0816.0-0736', 'SDSSJ08566+0140', 'S40954+65',
               'RXSJ12197-0314', '2E1228+1437', 'RXSJ13262+1230', 'RXSJ14164+2315', 'H1426+428', 'FIRSTJ15106+3335',
               'RXSJ00274+2607', 'SHBLJ01150-3400', 'UGC842', 'MS02057+3509', 'SDSSJ02208-0842', '3C66A', '1ES0229+200',
               'FIRSTJ02532-0124', '1WGAJ0421.5+1433', 'SHBLJ04414+1504', 'RXSJ06309-2406', 'MS07379+7441',
               'RXSJ07546+3911', 'SHBLJ07534+2921', 'TEX0836+182', 'B20912+29', 'SDSSJ10387+3927', 'SDSSJ10489+5009',
               '1WGAJ1057.6-7724', '2QZJ113045+0055', 'SDSSJ11418+0219', 'SDSSJ12039+5819', '1207+39W4', 'ON231',
               'MS12292+6430', 'SDSSJ12315+0138', 'SHBLJ12351-1403', 'XBSJ13304+2415', 'SDSSJ14067+5308',
               '2QZJ142701-0123', 'PG1553+11', 'TEX2013+370', 'MH2136-428', 'RXSJ22111-0003', 'SDSSJ22149+0020',
               'PKS2316-423', 'QJ2319+161']

    bll_catalog = fits.open('/home/aaranda/tfm/bllacs_PN_NopileupNofasttiming.fits')
    data = bll_catalog[1].data
    obsid_list = []
    for row in data:
        if row[10] != "PrimeSmallWindow":
            if row[0] in bl_lacs:
                obsid_list.append(row[5])
    return obsid_list

def my_custom_logger(logger_name, level=logging.INFO):
    """
    Method to return a custom logger with the given name and level
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    format_string = '%(asctime)s - %(message)s'
    log_format = logging.Formatter(format_string)
    # # Creating and adding the console handler
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setFormatter(log_format)
    # logger.addHandler(console_handler)
    # Creating and adding the file handler
    file_handler = logging.FileHandler(logger_name, mode='a')
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    return logger