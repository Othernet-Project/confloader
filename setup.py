import os
from setuptools import setup

import confloader as mod


def read(fname):
        """ Return content of specified file """
        return open(os.path.join(os.path.dirname(__file__), fname)).read()


VERSION = mod.__version__

setup(
    name='confloader',
    version=VERSION,
    license='GPL',
    description=('Python module for loading .ini configuration files with '
                 'extra bells and whistles.'),
    long_description=read('README.rst'),
    py_modules=[mod.__name__],
    classifiers=[
        'Development Status :: 1 - Pre Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
)
