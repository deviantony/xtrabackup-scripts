import subprocess
from xtrabackup.exception import ProcessError


class CommandExecutor:

    def __init__(self, output_file_path):
        self.output_file_path = output_file_path

    def exec_command(self, command):
        with open(self.output_file_path, 'a+') as error_file:
            process = subprocess.Popen(command, stdout=error_file,
                                       stderr=subprocess.STDOUT)
            process.communicate()
            if process.returncode != 0:
                raise ProcessError(command, process.returncode)

    def exec_filesystem_backup(self, user, password,
                               threads, backup_directory):
        command = [
            'innobackupex',
            '--user=' + user,
            '--parallel=' + threads,
            '--no-lock',
            '--no-timestamp',
            backup_directory]
        if password:
            command.append('--password=' + password)
        self.exec_command(command)

    def exec_incremental_backup(self, user, password,
                                threads, lsn, backup_directory):
        command = [
            'innobackupex',
            '--user=' + user,
            '--parallel=' + threads,
            '--incremental',
            '--incremental-lsn=' + lsn,
            '--no-lock',
            '--no-timestamp',
            '--incremental-force-scan',
            backup_directory]
        if password:
            command.append('--password=' + password)
        self.exec_command(command)

    def exec_backup_preparation(self, backup_directory, redo_logs):
        command = [
            'innobackupex',
            '--apply-log',
            backup_directory]
        if redo_logs:
            command.append('--redo-only')
        self.exec_command(command)

    def exec_incremental_preparation(self, backup_directory,
                                     incremental_directory):
        command = [
            'innobackupex',
            '--apply-log',
            '--redo-only',
            '--incremental-dir=' + incremental_directory,
            backup_directory]
        self.exec_command(command)

    def exec_manage_service(self, service_name, action):
        command = ['service', service_name, action]
        self.exec_command(command)

    def exec_chown(self, user, group, directory_path):
        command = ['/bin/chown', '-R', user + ':' + group, directory_path]
        self.exec_command(command)

    def create_archive(self, directory, archive_path, compress):
        if compress:
            tar_options = 'cpvzf'
        else:
            tar_options = 'cpvf'
        command = [
            'tar',
            tar_options,
            archive_path,
            '-C',
            directory, '.']
        self.exec_command(command)

    def extract_archive(self, archive_path, destination_path, compressed):
        if compressed:
            tar_options = 'xpvzf'
        else:
            tar_options = 'xpvf'
        command = [
            'tar',
            tar_options,
            archive_path,
            '-C',
            destination_path]
        self.exec_command(command)
