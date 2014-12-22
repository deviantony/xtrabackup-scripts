import subprocess
from xtrabackup.exception import CommandError


class CommandExecutor:

    def __init__(self, error_file_path):
        self.error_file_path = error_file_path

    def exec_command(self, command):
        with open(self.error_file_path, 'a+') as error_file:
            process = subprocess.Popen(command, stdout=error_file,
                                       stderr=subprocess.STDOUT)
            process.communicate()
            if process.returncode != 0:
                raise CommandError(command, process.returncode)

    def exec_enhanced_fs_backup(self, user, password,
                                threads, backup_directory):
        command = [
            'innobackupex',
            '--user=' + user,
            '--parallel=' + threads,
            '--no-lock',
            '--no-timestamp',
            backup_directory]
        self.exec_command(command)

    def exec_filesystem_backup(self, user, password,
                               threads, backup_directory):
        log = open('/var/log/pyxtrabackup.log', 'a')
        if password:
            subprocess.check_output([
                'innobackupex',
                '--user=' + user,
                '--password=' + password,
                '--parallel=' + threads,
                '--no-lock',
                '--no-timestamp',
                backup_directory], stderr=subprocess.STDOUT)
        else:
            subprocess.check_output([
                'innobackupex',
                '--user=' + user,
                '--parallel=' + threads,
                '--no-lock',
                '--no-timestamp',
                backup_directory], stderr=log)

    def exec_incremental_backup(self, user, password,
                                threads, lsn, backup_directory):
        if password:
            subprocess.check_output([
                'innobackupex',
                '--user=' + user,
                '--password=' + password,
                '--parallel=' + threads,
                '--incremental',
                '--incremental-lsn=' + lsn,
                '--no-lock',
                '--no-timestamp',
                backup_directory], stderr=subprocess.STDOUT)
        else:
            subprocess.check_output([
                'innobackupex',
                '--user=' + user,
                '--parallel=' + threads,
                '--incremental',
                '--incremental-lsn=' + lsn,
                '--no-lock',
                '--no-timestamp',
                backup_directory], stderr=subprocess.STDOUT)

    def exec_backup_preparation(self, backup_directory, redo_logs):
        if redo_logs:
            subprocess.check_output([
                'innobackupex',
                '--apply-log',
                '--redo-only',
                backup_directory], stderr=subprocess.STDOUT)
        else:
            subprocess.check_output([
                'innobackupex',
                '--apply-log',
                backup_directory], stderr=subprocess.STDOUT)

    def exec_incremental_preparation(self, backup_directory,
                                     incremental_directory):
        subprocess.check_output([
            'innobackupex',
            '--apply-log',
            '--redo-only',
            '--incremental-dir=' + incremental_directory,
            backup_directory], stderr=subprocess.STDOUT)

    def exec_manage_service(self, service_name, action):
        subprocess.check_output([
            '/etc/init.d/' + service_name,
            action], stderr=subprocess.STDOUT)

    def exec_chown(self, user, group, directory_path):
        subprocess.check_output([
            '/bin/chown',
            '-R',
            user + ':' + group,
            directory_path], stderr=subprocess.STDOUT)

    def create_archive(self, directory, archive_path):
        subprocess.check_output([
            'tar',
            'cpvzf',
            archive_path,
            '-C',
            directory, '.'], stderr=subprocess.STDOUT)

    def extract_archive(self, archive_path, destination_path):
        subprocess.check_output([
            'tar',
            'xpvzf',
            archive_path,
            '-C',
            destination_path], stderr=subprocess.STDOUT)
