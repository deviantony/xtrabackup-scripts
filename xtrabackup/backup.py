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
import sys
import logging
from .tools import BackupTool


def main():
    arguments = docopt(__doc__, version='1.0')
    backup_tool = BackupTool(arguments['--log-file'])
    try:
        backup_tool.check_prerequisites(arguments['<repository>'])
        backup_tool.prepare_workdir(arguments['--tmp-dir'])
        backup_tool.exec_backup(arguments['--user'],
                                arguments['--password'],
                                arguments['--backup-threads'])
        backup_tool.prepare_backup()
        backup_tool.compress_backup()
        backup_tool.transfer_backup(arguments['<repository>'])
        backup_tool.clean()
    except Exception:
        logger = logging.getLogger(__name__)
        logger.error("An error occured during the backup process.",
                     exc_info=True)
        exit(1)
    exit(0)


if __name__ == '__main__':
    sys.exit(main())
