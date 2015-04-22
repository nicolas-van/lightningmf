#! /usr/bin/python
# -*- coding: utf-8 -*-
from setuptools import setup
import os.path

setup(name='lightningmf',
    version='1.0.5',
    description='Lightning MAME Frontend',
    author='Nicolas Vanhoren',
    author_email='nicolas.vanhoren@unknown.com',
    url='http://lightningmf.neoname.eu/',
    packages=["lightningmf_pk"],
    scripts=["lightningmf"],
    package_data={'lightningmf_pk': ["*.ui", "*.svg", "*.png"]},
    long_description="Lightning MAME Frontend is a simple and effective MAME Frontend.",
    keywords="",
    license="GPLv3",
    install_requires=[
        "SqlAlchemy>=1.0.0",
    ],
)

