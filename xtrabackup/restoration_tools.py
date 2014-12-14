import xtrabackup.command_executor as command_executor
import xtrabackup.filesystem_utils as filesystem_utils
import xtrabackup.log_manager as log_manager
import xtrabackup.timer as timer
import logging
from subprocess import CalledProcessError
from sys import stdout


class RestorationTool:

    def __init__(self, log_file, data_dir):
        self.log_manager = log_manager.LogManager()
        self.data_dir = data_dir
        self.stop_watch = timer.Timer()
        self.setup_logging(log_file)

    def setup_logging(self, log_file):
        self.logger = logging.getLogger(__name__)
        self.log_manager.attach_file_handler(self.logger, log_file)

    def prepare_workdir(self, path):
        self.workdir = path + '/pyxtrabackup-restore'
        filesystem_utils.mkdir_path(self.workdir, 0o755)
        self.logger.debug("Temporary workdir: " + self.workdir)

    def stop_service(self):
        try:
            command_executor.exec_manage_service('mysql', 'stop')
        except:
            self.logger.error(
                'Unable to manage MySQL service.',
                exc_info=True)
            self.clean()
            raise

    def clean_data_dir(self):
        try:
            filesystem_utils.clean_directory(self.data_dir)
        except:
            self.logger.error(
                'Unable to clean MySQL data directory.',
                exc_info=True)
            self.clean()
            raise

    def restore_base_backup(self, archive_path):
        self.stop_watch.start_timer()
        try:
            command_executor.extract_archive(archive_path, self.data_dir)
            command_executor.exec_backup_preparation(self.data_dir, True)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the base backup restoration process.',
                exc_info=True)
            self.logger.error(
                'Command output: %s', e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Base backup restoration time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def restore_incremental_backups(self, incremental_archive):
        try:
            repository, archive_name = filesystem_utils.split_path(
                incremental_archive)
            incremental_target = int(archive_name.split('_')[1])
            for step in range(1, incremental_target + 1):
                self.restore_incremental_backup(repository, step)
        except:
            self.logger.error(
                'An error occured during the incremental\
                 backups restoration process.',
                exc_info=True)
            self.clean()
            raise

    def restore_incremental_backup(self, archive_repository, incremental_step):
        self.stop_watch.start_timer()
        try:
            prefix = ''.join(['inc_', str(incremental_step), '_'])
            backup_archive = filesystem_utils.get_prefixed_file_in_dir(
                archive_repository, prefix)
            extracted_archive_path = ''.join([self.workdir, '/',
                                              prefix, 'archive'])
            filesystem_utils.mkdir_path(extracted_archive_path, 0o755)
            command_executor.extract_archive(backup_archive,
                                             extracted_archive_path)
            command_executor.exec_incremental_preparation(
                self.data_dir,
                extracted_archive_path)
        except:
            self.logger.error(
                'An error occured during an incremental backup restoration.',
                exc_info=True)
            self.clean()
            raise
        self.logger.info("Incremental step #%s restoration time: %s\
 - Duration: %s",
                         incremental_step,
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def prepare_data_dir(self):
        try:
            command_executor.exec_backup_preparation(self.data_dir, False)
        except:
            self.logger.error(
                'An error occured during the backup final preparation.',
                exc_info=True)
            self.clean()
            raise
        self.logger.info("Backup final preparation time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def set_data_dir_permissions(self):
        try:
            command_executor.exec_chown('mysql', 'mysql', self.data_dir)
        except:
            self.logger.error('Unable to reset MySQL data dir permissions.',
                              exc_info=True)
            self.clean()
            raise

    def start_service(self):
        try:
            command_executor.exec_manage_service('mysql', 'start')
        except:
            self.logger.error(
                'Unable to manage MySQL service.',
                exc_info=True)
            self.clean()
            raise

    def clean(self):
        filesystem_utils.delete_directory(self.workdir)
