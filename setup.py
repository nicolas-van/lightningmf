#! /usr/bin/python
# -*- coding: utf-8 -*-
from distutils.core import setup
import os.path

setup(name='lightningmf',
      version='1.0.1',
      description='Lightning MAME Frontend',
      author='Nicolas Vanhoren',
      author_email='nicolas.vanhoren@unknown.com',
      url='http://nicolas-van.github.com/lightningmf',
      packages=["lightningmf_pk"],
      scripts=["lightningmf"],
      package_data={'lightningmf_pk': ["*.ui", "*.svg"]},
      long_description="Lightning MAME Frontend is a simple and effective MAME Frontend.",
      keywords="",
      license="GPLv3",
      classifiers=[
          ],
     )

