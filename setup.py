from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='xtrabackup-py',

    version='3.0.0b1',

    description='Percona xtrabackup wrapper.',
    long_description=long_description,

    url='https://github.com/deviantony/xtrabackup-scripts',

    author='Anthony Lapenna',
    author_email='lapenna.anthony@gmail.com',

    license='Apache 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: System Administrators',
        'Topic :: System :: Archiving :: Backup',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='mysql database backup percona xtrabackup',

    packages=find_packages(exclude=['contrib', 'docs', 'tests*', 'sql']),

    install_requires=['docopt'],

    # extras_require = {
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'py-xtrabackup=xtrabackup:__main__',
        ],
    },
)
