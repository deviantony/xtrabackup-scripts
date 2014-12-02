from setuptools import setup, find_packages
import os

pkg_root = os.path.dirname(__file__)

# Error-handling here is to allow package to be built w/o README included
try:
    long_description = open(os.path.join(pkg_root, 'DESCRIPTION.rst')).read()
except IOError:
    long_description = ''

setup(
    name='pyxtrabackup',

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

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
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

    entry_points={
        'console_scripts': [
            'pyxtrabackup=xtrabackup.backup:main',
        ],
    },
)
