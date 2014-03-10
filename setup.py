# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from distutils.core import setup

setup(name='tjjrbot',
      version='0.1.0',
      description='Simple but elegant IRC bot.',
      author='Tuomas Räsänen',
      author_email='tuomasjjrasanen@tjjr.fi',
      url='http://tjjr.fi/sw/tjjrbot/',
      license='GPLv3+',
      py_modules=['tjjrbot'],
      scripts=["tjjrbot"],
      platforms=['Linux'],
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: POSIX :: Linux",
          "Topic :: Communications :: Chat :: Internet Relay Chat",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
      ],
)
