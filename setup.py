import os
from setuptools import setup

import confloader as mod


def read(fname):
        """ Return content of specified file """
        return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='confloader',
    description=('Python module for loading .ini configuration files with '
                 'extra bells and whistles.'),
    keywords='configuration ini confloader',
    version=mod.__version__,
    author='Outernet Inc',
    author_email='apps@outernet.is',
    license='BSD',
    url='https://github.com/Outernet-Project/confloader',
    long_description=read('README.rst'),
    py_modules=[mod.__name__],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)
