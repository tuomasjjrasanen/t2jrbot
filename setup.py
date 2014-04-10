# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from distutils.core import setup

setup(name='t2jrbot',
      version='0.1.0',
      description='Simple but elegant IRC bot.',
      author='Tuomas Räsänen',
      author_email='tuomasjjrasanen@tjjr.fi',
      url='http://tjjr.fi/sw/t2jrbot/',
      license='GPLv3+',
      package_dir={'t2jrbot': 'lib'},
      packages=['t2jrbot', 't2jrbot.plugins'],
      scripts=["bin/t2jrbot"],
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
      data_files=[
        ("etc/t2jrbot", ["t2jrbot.yaml"]),
        ],
)
