import errno
import os
import subprocess
import datetime
from distutils import spawn
from xtrabackup.exception import ProgramError


def create_sub_repository(repository_path):
    sub_repository = ''.join([
        repository_path,
        '/',
        datetime.datetime.now().strftime("%Y%m%d")])
    mkdir_path(sub_repository, 0o755)
    return sub_repository


def prepare_archive_path(archive_sub_repository):
    archive_path = ''.join([
        archive_sub_repository,
        '/backup_',
        datetime.datetime.now().strftime("%Y%m%d_%H%M"),
        '.tar.gz'])
    return archive_path


def create_archive(directory, archive_path):
    subprocess.check_output([
        'tar',
        'cpfvz',
        archive_path,
        '-C',
        directory, '.'], stderr=subprocess.STDOUT)


def mkdir_path(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def check_required_binaries(binaries):
    for binary in binaries:
        if spawn.find_executable(binary) is None:
            raise ProgramError("Cannot locate binary: " + binary)


def check_path_existence(path):
    if not os.path.exists(path):
        raise ProgramError("Cannot locate folder: " + path)
