#!/usr/bin/env python3

"""Xtrabackup script

Usage:
  backup-fs.py <repository> --user=<user> [--password=<pwd>] [--tmp-dir=<tmp>] [--log-file=<log>] [--backup-threads=<threads>] 
  backup-fs.py (-h | --help)
  backup-fs.py --version


Options:
  -h --help                   Show this screen.
  --version                   Show version.
  --user=<user>               MySQL user.
  --password=<pwd>            MySQL password.
  --tmp-dir=<tmp>             Temp folder [default: /tmp].
  --log-file=<log>            Log file [default: /tmp/backup.log].
  --backup-threads=<threads>  Threads count [default: 1].

"""
from docopt import docopt
from system import *
from xtrabackup import *
import shutil

if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')
    # print(arguments)

    # Check for required binaries
    check_binary('innobackupex')
    check_binary('tar')

    # Check for backup repository existence
    check_folder(arguments['<repository>'])

    # Create tmp folder
    mkdir_p(arguments['--tmp-dir'], 0o755)

    # Prepare archive name and create timestamp folder in repository
    archive_path = prepare_archive(arguments['<repository>'])

    # Exec backup
    exec_filesystem_backup(
        arguments['--user'],
        arguments['--password'],
        arguments['--backup-threads'],
        arguments['--tmp-dir'] + '/backup')

    # Apply phasis
    exec_backup_preparation(arguments['--tmp-dir'] + '/backup')

    # Exec tar
    create_archive(
        arguments['--tmp-dir'] + '/backup',
        arguments['--tmp-dir'] + '/backup.tar.gz')

    # Move backup from tmp folder to repository
    shutil.move(arguments['--tmp-dir'] + '/backup.tar.gz', archive_path)

    # Remove tmp folder
    shutil.rmtree(arguments['--tmp-dir'] + '/backup')

    exit(0)
