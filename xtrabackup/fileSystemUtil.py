import errno
import os
import shutil
import subprocess
import datetime
from exception import ProgramError


class FileSystemUtil:

    def create_sub_repository(self, repository_path):
        sub_repository = ''.join([
            repository_path,
            '/',
            datetime.datetime.now().strftime("%Y%m%d")])
        self.mkdir_path(sub_repository, 0o755)
        return sub_repository

    def prepare_archive_path(self, archive_sub_repository):
        archive_path = ''.join([
            archive_sub_repository,
            '/backup_',
            datetime.datetime.now().strftime("%Y%m%d_%H%M"),
            '.tar.gz'])
        return archive_path

    def create_archive(self, directory, archive_path):
        subprocess.check_output([
            'tar',
            'cpfvz',
            archive_path,
            '-C',
            directory, '.'], stderr=subprocess.STDOUT)

    def mkdir_path(self, path, mode):
        try:
            os.makedirs(path, mode)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def check_required_binaries(self, binaries):
        """ Check binary method supported by Python >= 3.4 only """
        for binary in binaries:
            if not shutil.which(binary):
                raise ProgramError("Cannot locate binary: " + binary)

    def check_path_existence(self, path):
        if not os.path.exists(path):
            raise ProgramError("Cannot locate folder: " + path)
