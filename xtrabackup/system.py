import errno
import os
import shutil

from exception import ProgramError


def mkdir_p(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def check_binary(binary):
    """ Check binary method supported by Python 3.4 only """
    if not shutil.which(binary):
        raise ProgramError("Cannot locate binary: " + binary, None)


def check_folder(path):
    if not os.path.exists(path):
        raise ProgramError("Cannot locate folder: " + path, None)
