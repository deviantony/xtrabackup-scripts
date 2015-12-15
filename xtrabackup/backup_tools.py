from xtrabackup.command_executor import CommandExecutor
from xtrabackup.exception import ProcessError
from xtrabackup.http_manager import HttpManager
import xtrabackup.filesystem_utils as filesystem_utils
import xtrabackup.log_manager as log_manager
import xtrabackup.exception as exception
import xtrabackup.timer as timer
import logging


class BackupTool:

    def __init__(self, log_file, output_file, no_compression, debug=False):
        self.debug = debug
        self.log_manager = log_manager.LogManager()
        self.stop_watch = timer.Timer()
        self.setup_logging(log_file)
        try:
            with open(output_file, 'a+'):
                pass
        except Exception as error:
            self.logger.error('Output file error: %s', str(error),
                              exc_info=self.debug)
            raise
        self.command_executor = CommandExecutor(output_file)
        self.compress = not no_compression
        self.http = HttpManager()

    def setup_logging(self, log_file):
        self.logger = logging.getLogger(__name__)
        self.log_manager.attach_file_handler(self.logger, log_file)

    def check_prerequisites(self, repository):
        try:
            filesystem_utils.check_required_binaries(['innobackupex', 'tar'])
            filesystem_utils.check_path_existence(repository)
        except exception.ProgramError as error:
            self.logger.error('Prerequisites check failed. %s', str(error),
                              exc_info=self.debug)
            raise

    def prepare_workdir(self, path):
        try:
            filesystem_utils.mkdir_path(path, 0o755)
        except exception.ProgramError:
            self.logger.error('Workdir preparation failed.',
                              exc_info=self.debug)
            raise
        self.workdir = path + '/xtrabackup_tmp'
        self.logger.debug("Temporary workdir: " + self.workdir)
        if self.compress:
            self.archive_path = path + '/backup.tar.gz'
        else:
            self.archive_path = path + '/backup.tar'
        self.logger.debug("Temporary archive: " + self.archive_path)

    def prepare_repository(self, repository, incremental):
        if incremental:
            sub_directory = '/INC'
        else:
            sub_directory = ''
        try:
            self.backup_repository = filesystem_utils.create_sub_repository(
                repository, sub_directory)
        except exception.ProgramError:
            self.logger.error('Unable to create repository.',
                              exc_info=self.debug)
            raise

    def prepare_archive_name(self, incremental, incremental_cycle):
        if incremental:
            backup_prefix = ''.join(['inc_', str(self.incremental_step), '_'])
        else:
            if incremental_cycle:
                backup_prefix = 'base_'
            else:
                backup_prefix = ''
        self.final_archive_path = filesystem_utils.prepare_archive_path(
            self.backup_repository, backup_prefix, self.compress)

    def exec_incremental_backup(self, user, password, thread_count):
        self.stop_watch.start_timer()
        try:
            self.command_executor.exec_incremental_backup(
                user,
                password,
                thread_count,
                self.last_lsn,
                self.workdir)
        except ProcessError:
            self.logger.error(
                'An error occured during the incremental backup process.',
                exc_info=self.debug)
            self.clean()
            raise
        self.logger.info("Incremental backup time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def exec_full_backup(self, user, password, thread_count):
        self.stop_watch.start_timer()
        try:
            self.command_executor.exec_filesystem_backup(
                user,
                password,
                thread_count,
                self.workdir)
        except ProcessError:
            self.logger.error(
                'An error occured during the backup process.',
                exc_info=self.debug)
            self.clean()
            raise
        self.logger.info("Backup time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def prepare_backup(self, redo_logs):
        self.stop_watch.start_timer()
        try:
            self.command_executor.exec_backup_preparation(self.workdir,
                                                          redo_logs)
        except ProcessError:
            self.logger.error(
                'An error occured during the preparation process.',
                exc_info=self.debug)
            self.clean()
            raise
        self.logger.info("Backup preparation time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def archive_backup(self):
        self.stop_watch.start_timer()
        try:
            self.command_executor.create_archive(
                self.workdir, self.archive_path, self.compress)
        except ProcessError:
            self.logger.error(
                'An error occured during the archiving of the backup.',
                exc_info=self.debug)
            self.clean()
            raise
        self.logger.info("Backup archiving time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def transfer_backup(self, repository):
        self.stop_watch.start_timer()
        try:
            self.logger.debug("Archive path: " + self.final_archive_path)
            filesystem_utils.move_file(self.archive_path,
                                       self.final_archive_path)
        except Exception:
            self.logger.error(
                'An error occured during the backup transfer.',
                exc_info=self.debug)
            self.clean()
            raise
        self.logger.info("Archive copy time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def clean(self):
        filesystem_utils.delete_directory_if_exists(self.workdir)

    def trigger_webhook(self, webhook_url):
        postdata = {
            'archive_repository': self.backup_repository,
            'archive_path': self.final_archive_path,
        }
        self.logger.debug("POST archive_repository: " + self.backup_repository)
        self.logger.debug("POST archive_path: " + self.final_archive_path)
        self.http.post(webhook_url, postdata)

    def save_incremental_data(self, incremental):
        try:
            if incremental:
                self.incremental_step += 1
            else:
                self.incremental_step = 0
            self.last_lsn = filesystem_utils.retrieve_value_from_file(
                self.workdir + '/xtrabackup_checkpoints',
                '^to_lsn = (\d+)$')
            filesystem_utils.write_array_to_file(
                '/var/tmp/pyxtrabackup-incremental',
                ['BASEDIR=' + self.backup_repository,
                 'LSN=' + self.last_lsn,
                 'INCREMENTAL_STEP=' + str(self.incremental_step)])
        except:
            self.logger.error(
                'Unable to save the incremental backup data.',
                exc_info=self.debug)
            self.clean()
            raise

    def load_incremental_data(self):
        try:
            self.base_dir = filesystem_utils.retrieve_value_from_file(
                '/var/tmp/pyxtrabackup-incremental',
                '^BASEDIR=(.*)$')
            self.last_lsn = filesystem_utils.retrieve_value_from_file(
                '/var/tmp/pyxtrabackup-incremental',
                '^LSN=(\d+)$')
            self.incremental_step = int(
                filesystem_utils.retrieve_value_from_file(
                    '/var/tmp/pyxtrabackup-incremental',
                    '^INCREMENTAL_STEP=(\d+)$'))
        except:
            self.logger.error(
                'Unable to load the incremental backup data.',
                exc_info=self.debug)
            self.clean()
            raise

    def start_full_backup(self, repository, workdir, user,
                          password, threads, webhook):
        self.check_prerequisites(repository)
        self.prepare_workdir(workdir)
        self.prepare_repository(repository, False)
        self.prepare_archive_name(False, False)
        self.exec_full_backup(user, password, threads)
        self.prepare_backup(False)
        self.archive_backup()
        self.transfer_backup(repository)
        self.clean()
        if webhook:
            self.trigger_webhook(webhook)

    def start_incremental_backup(self, repository, incremental,
                                 workdir, user, password, threads):
        self.check_prerequisites(repository)
        self.prepare_workdir(workdir)
        self.prepare_repository(repository, True)
        if incremental:
            self.load_incremental_data()
            self.prepare_archive_name(incremental, True)
            self.exec_incremental_backup(user, password, threads)
        else:
            self.prepare_archive_name(incremental, True)
            self.exec_full_backup(user, password, threads)
        self.save_incremental_data(incremental)
        self.archive_backup()
        self.transfer_backup(repository)
        self.clean()
