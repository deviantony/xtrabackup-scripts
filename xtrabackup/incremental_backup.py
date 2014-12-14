"""Xtrabackup script

Usage:
    pyxtrabackup-inc <repository> --user=<user> [--password=<pwd>] [--incremental] [--tmp-dir=<tmp>] [--log-file=<log>] [--backup-threads=<threads>] 
    pyxtrabackup-inc (-h | --help)
    pyxtrabackup --version


Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --user=<user>               MySQL user.
    --password=<pwd>            MySQL password.
    --incremental               Start an incremental cycle.
    --tmp-dir=<tmp>             Temporary directory [default: /tmp].
    --log-file=<log>            Log file [default: /var/log/pyxtrabackup.log].
    --backup-threads=<threads>  Threads count [default: 1].

"""
from docopt import docopt
import sys
import logging
from xtrabackup.backup_tools import BackupTool


def main():
    arguments = docopt(__doc__, version='1.0')
    backup_tool = BackupTool(arguments['--log-file'])
    try:
        backup_tool.check_prerequisites(arguments['<repository>'])
        backup_tool.prepare_workdir(arguments['--tmp-dir'])
        backup_tool.prepare_repository(arguments['<repository>'], True)
        if arguments['--incremental']:
            backup_tool.load_incremental_data()
            backup_tool.exec_incremental_backup(arguments['--user'],
                                                arguments['--password'],
                                                arguments['--backup-threads'])
        else:
            backup_tool.exec_full_backup(arguments['--user'],
                                         arguments['--password'],
                                         arguments['--backup-threads'])
        backup_tool.save_incremental_data(arguments['--incremental'])
        backup_tool.compress_backup()
        backup_tool.prepare_archive_name(arguments['--incremental'], True)
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
