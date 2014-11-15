import subprocess


def exec_filesystem_backup(user, password, threads, backup_directory):
    if password:
        subprocess.check_call([
            'innobackupex',
            '--user=' + user,
            '--password=' + password,
            '--parallel=' + threads,
            '--no-lock',
            '--no-timestamp',
            backup_directory])
    else:
        subprocess.check_call([
            'innobackupex',
            '--user=' + user,
            '--parallel=' + threads,
            '--no-lock',
            '--no-timestamp',
            backup_directory])


def exec_backup_preparation(backup_directory):
    subprocess.check_call([
        'innobackupex',
        '--apply-log',
        backup_directory])
