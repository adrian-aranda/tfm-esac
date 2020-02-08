import os
import subprocess


def sasinit(sas_dir):
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
