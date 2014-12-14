import xtrabackup.command_executor as command_executor
import xtrabackup.filesystem_utils as filesystem_utils
import xtrabackup.log_manager as log_manager
import xtrabackup.exception as exception
import xtrabackup.timer as timer
import logging
from subprocess import CalledProcessError
from sys import stdout


class BackupTool:

    def __init__(self, log_file):
        self.log_manager = log_manager.LogManager()
        self.stop_watch = timer.Timer()
        self.setup_logging(log_file)

    def setup_logging(self, log_file):
        self.logger = logging.getLogger(__name__)
        self.log_manager.attach_file_handler(self.logger, log_file)

    def check_prerequisites(self, repository):
        try:
            filesystem_utils.check_required_binaries(['innobackupex', 'tar'])
            filesystem_utils.check_path_existence(repository)
        except exception.ProgramError:
            self.logger.error('Prerequisites check failed.', exc_info=True)
            raise

    def prepare_workdir(self, path):
        filesystem_utils.mkdir_path(path, 0o755)
        self.workdir = path + '/xtrabackup_tmp'
        self.logger.debug("Temporary workdir: " + self.workdir)
        self.archive_path = path + '/backup.tar.gz'
        self.logger.debug("Temporary archive: " + self.archive_path)

    def prepare_repository(self, repository, incremental):
        if incremental:
            sub_folder = '/INC'
        else:
            sub_folder = ''
        self.backup_repository = filesystem_utils.create_sub_repository(
            repository, sub_folder)

    def prepare_archive_name(self, incremental, incremental_cycle):
        if incremental:
            backup_prefix = ''.join(['inc_', str(self.incremental_step), '_'])
        else:
            if incremental_cycle:
                backup_prefix = 'base_'
            else:
                backup_prefix = ''
        self.final_archive_path = filesystem_utils.prepare_archive_path(
            self.backup_repository, backup_prefix)

    def exec_incremental_backup(self, user, password, thread_count):
        self.stop_watch.start_timer()
        try:
            command_executor.exec_incremental_backup(
                user,
                password,
                thread_count,
                self.last_lsn,
                self.workdir)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the incremental backup process.',
                exc_info=True)
            self.logger.error(
                'Command output: %s', e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Incremental backup time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def exec_full_backup(self, user, password, thread_count):
        self.stop_watch.start_timer()
        try:
            command_executor.exec_filesystem_backup(
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
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def prepare_backup(self, redo_logs):
        self.stop_watch.start_timer()
        try:
            command_executor.exec_backup_preparation(self.workdir, redo_logs)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the preparation process.',
                exc_info=True)
            self.logger.error(
                'Command output: %s', e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Backup preparation time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def compress_backup(self):
        self.stop_watch.start_timer()
        try:
            filesystem_utils.create_archive(self.workdir, self.archive_path)
        except CalledProcessError as e:
            self.logger.error(
                'An error occured during the backup compression.',
                exc_info=True)
            self.logger.error('Command output: %s',
                              e.output.decode(stdout.encoding))
            self.clean()
            raise
        self.logger.info("Backup compression time: %s - Duration: %s",
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
                'An error occured during the backup compression.',
                exc_info=True)
            self.clean()
            raise
        self.logger.info("Archive copy time: %s - Duration: %s",
                         self.stop_watch.stop_timer(),
                         self.stop_watch.duration_in_seconds())

    def clean(self):
        filesystem_utils.delete_directory(self.workdir)

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
                exc_info=True)
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
                exc_info=True)
            self.clean()
            raise


class RestoreTool:

    def __init__(self, log_file):
        self.log_manager = log_manager.LogManager()
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
            filesystem_utils.clean_directory('/var/lib/mysql')
        except:
            self.logger.error(
                'Unable to clean MySQL data directory.',
                exc_info=True)
            self.clean()
            raise

    def restore_base_backup(self, archive_path):
        self.stop_watch.start_timer()
        try:
            filesystem_utils.extract_archive(archive_path, '/var/lib/mysql')
            command_executor.exec_backup_preparation('/var/lib/mysql', True)
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
            filesystem_utils.extract_archive(backup_archive,
                                             extracted_archive_path)
            command_executor.exec_incremental_preparation(
                '/var/lib/mysql',
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
            command_executor.exec_backup_preparation('/var/lib/mysql', False)
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
            command_executor.exec_chown('mysql', 'mysql', '/var/lib/mysql')
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
