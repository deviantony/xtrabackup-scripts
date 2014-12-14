"""Xtrabackup script

Usage:
    pyxtrabackup-restore --base-archive=<base_archive_path> --incremental-archive=<incremental_archive_path> --user=<user> [--password=<pwd>] [--data-dir=<data_dir>] [--restart] [--tmp-dir=<tmp>] [--log-file=<log>] [--backup-threads=<threads>]
    pyxtrabackup-restore (-h | --help)
    pyxtrabackup --version


Options:
    -h --help                                   Show this screen.
    --version                                   Show version.
    --user=<user>                               MySQL user.
    --password=<pwd>                            MySQL password.
    --base-archive=<archive_path>               Base backup.
    --incremental-archive=<archive_path>        Incremental archive target.
    --data-dir=<data_dir>                       MySQL server data directory [default: /var/lib/mysql]
    --restart                                   Restart the server after backup restoration.
    --tmp-dir=<tmp>                             Temporary directory [default: /tmp].
    --log-file=<log>                            Log file [default: /var/log/pyxtrabackup-restore.log].
    --backup-threads=<threads>                  Threads count [default: 1].

"""
from docopt import docopt
import sys
import logging
from xtrabackup.restoration_tools import RestorationTool


def main():
    arguments = docopt(__doc__, version='1.0')
    restore_tool = RestorationTool(arguments['--log-file'],
                                   arguments['--data-dir'])
    try:
        restore_tool.prepare_workdir(arguments['--tmp-dir'])
        restore_tool.stop_service()
        restore_tool.clean_data_dir()
        restore_tool.restore_base_backup(arguments['--base-archive'])
        restore_tool.restore_incremental_backups(
            arguments['--incremental-archive'])
        restore_tool.prepare_data_dir()
        restore_tool.set_data_dir_permissions()
        restore_tool.clean()
        if arguments['--restart']:
            restore_tool.start_service()
    except Exception:
        logger = logging.getLogger(__name__)
        logger.error("An error occured during the restoration process.",
                     exc_info=True)
        exit(1)
    exit(0)


if __name__ == '__main__':
    sys.exit(main())
