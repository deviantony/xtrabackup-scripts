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
import log
import shutil
import system
import xtrabackup
import timer
import logging
import exception
from sys import stdout
from subprocess import CalledProcessError


def main(arguments):

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    log.attach_file_handler(logger, arguments['--log-file'])

    try:
        system.check_required_binaries(['innobackupex', 'tar'])
    except exception.ProgramError:
        logger.error('Missing binary.', exc_info=True)
        return 1

    try:
        system.check_path_existence(arguments['<repository>'])
    except exception.ProgramError:
        logger.error('Cannot locate repository.', exc_info=True)
        return 1

    system.mkdir_path(arguments['--tmp-dir'], 0o755)
    temporary_backup_directory = arguments['--tmp-dir'] + '/xtrabackup_tmp'
    logger.debug("Temporary_backup_directory: " + temporary_backup_directory)

    # Exec backup
    stopwatch = timer.Timer()
    stopwatch.start_timer()
    try:
        xtrabackup.exec_filesystem_backup(
            arguments['--user'],
            arguments['--password'],
            arguments['--backup-threads'],
            temporary_backup_directory)
    except CalledProcessError as e:
        logger.error(
            'An error occured during the backup process.', exc_info=True)
        logger.error('Command output: %s', e.output.decode(stdout.encoding))
        return 1
    logger.info("Backup time: %s - Duration: %s",
                stopwatch.stop_timer(), stopwatch.duration_in_seconds())

    # Prepare backup
    stopwatch.start_timer()
    try:
        xtrabackup.exec_backup_preparation(temporary_backup_directory)
    except CalledProcessError as e:
        logger.error(
            'An error occured during the preparation process.', exc_info=True)
        logger.error('Command output: %s', e.output.decode(stdout.encoding))
        return 1
    logger.info("Backup preparation time: %s - Duration: %s",
                stopwatch.stop_timer(), stopwatch.duration_in_seconds())

    # Compress backup
    temporary_backup_archive = arguments['--tmp-dir'] + '/backup.tar.gz'
    logger.debug("Temporary backup archive: " + temporary_backup_archive)
    stopwatch.start_timer()
    try:
        system.create_archive(
            temporary_backup_directory,
            temporary_backup_archive)
    except CalledProcessError as e:
        logger.error(
            'An error occured during the backup compression.', exc_info=True)
        logger.error('Command output: %s', e.output.decode(stdout.encoding))
        return 1
    logger.info("Backup compression time: %s - Duration: %s",
                stopwatch.stop_timer(), stopwatch.duration_in_seconds())

    # Move backup from temporary directory to repository
    stopwatch.start_timer()
    archive_sub_repository = system.create_sub_repository(
        arguments['<repository>'])
    archive_path = system.prepare_archive_path(archive_sub_repository)
    logger.debug("Archive path: " + archive_path)
    shutil.move(temporary_backup_archive, archive_path)
    logger.info("Archive copy time: %s - Duration: %s",
                stopwatch.stop_timer(), stopwatch.duration_in_seconds())

    # Clean temporary directory
    shutil.rmtree(temporary_backup_directory)

    exit(0)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')
    main(arguments)
