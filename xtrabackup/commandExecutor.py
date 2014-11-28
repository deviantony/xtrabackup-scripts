import subprocess


class CommandExecutor:

    def exec_filesystem_backup(user, password, threads, backup_directory):
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
                backup_directory], stderr=subprocess.STDOUT)

    def exec_backup_preparation(backup_directory):
        subprocess.check_output([
            'innobackupex',
            '--apply-log',
            backup_directory], stderr=subprocess.STDOUT)
