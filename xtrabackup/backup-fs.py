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
from timer import Timer
import shutil
import logging


if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler(arguments['--log-file'])
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    timer = Timer()

    check_required_binaries(['innobackupex', 'tar'])
    check_path_existence(arguments['<repository>'])
    mkdir_path(arguments['--tmp-dir'], 0o755)
    temporary_backup_directory = arguments['--tmp-dir'] + '/xtrabackup_tmp'
    logger.debug("Temporary_backup_directory: " + temporary_backup_directory)
    temporary_backup_archive = arguments['--tmp-dir'] + '/backup.tar.gz'
    logger.debug("Temporary backup archive: " + temporary_backup_archive)
    archive_sub_repository = create_sub_repository(arguments['<repository>'])
    archive_path = prepare_archive_path(archive_sub_repository)
    logger.debug("Archive path: " + archive_path)

    # Exec backup
    timer.start_timer()
    exec_filesystem_backup(
        arguments['--user'],
        arguments['--password'],
        arguments['--backup-threads'],
        temporary_backup_directory)
    logger.info("Backup time: %s - Duration: %s",
                timer.stop_timer(), timer.duration_in_seconds())

    # Prepare backup
    timer.start_timer()
    exec_backup_preparation(temporary_backup_directory)
    logger.info("Backup preparation time: %s - Duration: %s",
                timer.stop_timer(), timer.duration_in_seconds())

    # Compress backup
    timer.start_timer()
    create_archive(
        temporary_backup_directory,
        temporary_backup_archive)
    logger.info("Backup compression time: %s - Duration: %s",
                timer.stop_timer(), timer.duration_in_seconds())

    # Move backup from temporary directory to repository
    timer.start_timer()
    shutil.move(temporary_backup_archive, archive_path)
    logger.info("Archive copy time: %s - Duration: %s",
                timer.stop_timer(), timer.duration_in_seconds())

    # Clean temporary directory
    shutil.rmtree(temporary_backup_directory)

    exit(0)
