import subprocess


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


def exec_incremental_backup(user, password, threads, lsn, backup_directory):
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


def exec_backup_preparation(backup_directory, redo_logs):
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


def exec_manage_service(service_name, action):
    subprocess.check_output([
        '/etc/init.d/' + service_name,
        action], stderr=subprocess.STDOUT)
