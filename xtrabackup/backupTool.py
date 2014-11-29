import commandExecutor
import fileSystemUtil
import logManager
import exception
import logging
import timer
import shutil
from subprocess import CalledProcessError
from sys import stdout


class BackupTool:

    def __init__(self, log_file):
        self.log_manager = logManager.LogManager()
        self.stopWatch = timer.Timer()
        self.setup_logging(log_file)

    def setup_logging(self, log_file):
        self.logger = logging.getLogger(__name__)
        self.log_manager.attach_file_handler(self.logger, log_file)

    def check_prerequisites(self, repository):
        try:
            fileSystemUtil.check_required_binaries(['innobackupex', 'tar'])
            fileSystemUtil.check_path_existence(repository)
        except exception.ProgramError:
            self.logger.error('Prerequisites check failed.', exc_info=True)
            raise

    def prepare_workdir(self, path):
        fileSystemUtil.mkdir_path(path, 0o755)
        self.workdir = path + '/xtrabackup_tmp'
        self.logger.debug("Temporary workdir: " + self.workdir)
        self.archivePath = path + '/backup.tar.gz'
        self.logger.debug("Temporary archive: " + self.archivePath)

    def exec_backup(self, user, password, thread_count):
        self.stopWatch.start_timer()
        try:
            commandExecutor.exec_filesystem_backup(
                user,
                password,
                thread_count,
                self.workdir)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the backup process.', exc_info=True)
            self.logger.error(
                'Command output: %s', e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Backup time: %s - Duration: %s",
                         self.stopWatch.stop_timer(),
                         self.stopWatch.duration_in_seconds())

    def prepare_backup(self):
        self.stopWatch.start_timer()
        try:
            commandExecutor.exec_backup_preparation(self.workdir)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the preparation process.',
                exc_info=True)
            self.logger.error(
                'Command output: %s', e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Backup preparation time: %s - Duration: %s",
                         self.stopWatch.stop_timer(),
                         self.stopWatch.duration_in_seconds())

    def compress_backup(self):
        self.stopWatch.start_timer()
        try:
            fileSystemUtil.create_archive(self.workdir, self.archivePath)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the backup compression.',
                exc_info=True)
            self.logger.error('Command output: %s',
                              e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Backup compression time: %s - Duration: %s",
                         self.stopWatch.stop_timer(),
                         self.stopWatch.duration_in_seconds())

    def transfer_backup(self, repository):
        self.stopWatch.start_timer()
        try:
            backupRepository = fileSystemUtil.create_sub_repository(repository)
            finalArchivePath = fileSystemUtil.prepare_archive_path(
                backupRepository)
            self.logger.debug("Archive path: " + finalArchivePath)
            shutil.move(self.archivePath, finalArchivePath)
        except Exception:
            self.logger.error(
                'An error occured during the backup compression.',
                exc_info=True)
            self.clean()
            raise
        self.logger.info("Archive copy time: %s - Duration: %s",
                         self.stopWatch.stop_timer(),
                         self.stopWatch.duration_in_seconds())

    def clean(self):
        shutil.rmtree(self.workdir)
