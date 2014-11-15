import subprocess


def exec_backup(arguments):
    if arguments['--password']:
        subprocess.check_call([
            'innobackupex',
            '--user=' + arguments['--user'],
            '--password=' + arguments['--password'],
            '--parallel=' + arguments['--backup-threads'],
            '--no-lock',
            '--no-timestamp',
            arguments['--tmp-dir'] + '/backup'])
    else:
        subprocess.check_call([
            'innobackupex',
            '--user=' + arguments['--user'],
            '--parallel=' + arguments['--backup-threads'],
            '--no-lock',
            '--no-timestamp',
            arguments['--tmp-dir'] + '/backup'])


def exec_backup_apply(tmp_folder):
    subprocess.check_call(['innobackupex', '--apply-log', tmp_folder])
