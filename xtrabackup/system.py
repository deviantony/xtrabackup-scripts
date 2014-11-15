import errno
import os
import shutil
import subprocess
import datetime
from exception import ProgramError


def prepare_archive(repository_path):
    date = datetime.datetime.now()
    ts = date.strftime("%Y%m%d_%H%M")
    date_fmt = date.strftime("%Y%m%d")
    archive_name = 'backup_' + ts + '.tar.gz'
    archive_repository = repository_path + '/' + date_fmt
    archive_path = archive_repository + '/' + archive_name
    mkdir_p(archive_repository, 0o755)
    return archive_path


def create_archive(folder, archive_path):
    subprocess.check_call([
        'tar',
        'cpfvz',
        archive_path,
        '-C',
        folder, '.'])


def mkdir_p(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def check_binary(binary):
    """ Check binary method supported by Python >= 3.4 only """
    if not shutil.which(binary):
        raise ProgramError("Cannot locate binary: " + binary, None)


def check_folder(path):
    if not os.path.exists(path):
        raise ProgramError("Cannot locate folder: " + path, None)
