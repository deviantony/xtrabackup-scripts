import errno
import os
import datetime
from distutils import spawn
from xtrabackup.exception import ProgramError
from re import search
from shutil import rmtree, move
from glob import glob


def create_sub_repository(repository_path, sub_directory):
    sub_repository = ''.join([
        repository_path,
        '/',
        datetime.datetime.now().strftime("%Y%m%d"),
        sub_directory])
    mkdir_path(sub_repository, 0o755)
    return sub_repository


def prepare_archive_path(archive_sub_repository, prefix, compress):
    archive_path = ''.join([
        archive_sub_repository,
        '/',
        prefix,
        'backup_',
        datetime.datetime.now().strftime("%Y%m%d_%H%M")])
    if compress:
        archive_path = archive_path + '.tar.gz'
    else:
        archive_path = archive_path + '.tar'
    return archive_path


def mkdir_path(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise ProgramError("Unable to create directory: " + path)


def check_required_binaries(binaries):
    for binary in binaries:
        if spawn.find_executable(binary) is None:
            raise ProgramError("Cannot locate binary: " + binary)


def check_path_existence(path):
    if not os.path.exists(path):
        raise ProgramError("Cannot locate directory: " + path)


def retrieve_value_from_file(path, pattern):
    with open(path) as fp:
        for line in fp:
            value = search(pattern, line)
            if value:
                return value.group(1)


def write_array_to_file(path, array):
    with open(path, 'w') as fp:
        for item in array:
            fp.write(item + '\n')


def move_file(origin_path, destination_path):
    move(origin_path, destination_path)


def delete_directory_if_exists(path):
    if (os.path.isdir(path)):
        rmtree(path)


def clean_directory(path):
    for file_object in os.listdir(path):
        file_path = os.path.join(path, file_object)
        if os.path.islink(file_path) or os.path.isfile(file_path):
            os.unlink(file_path)
        else:
            rmtree(file_path)


def split_path(path):
    head, tail = os.path.split(path)
    return head, tail


def get_prefixed_file_in_dir(directory, prefix):
    files = glob(''.join([directory, '/', prefix, '*']))
    return files[0]
