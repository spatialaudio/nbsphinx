#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Use sphinx-quickstart to create your own conf.py file!
# After that, you have to edit a few things.  See below.

import sys
import os
from subprocess import check_output

# Add path to nbsphinx.py (if you didn't install it with pip):
sys.path.insert(0, os.path.abspath('..'))

# Select nbsphinx and, if needed, add a math extension (mathjax or pngmath):
extensions = [
    'nbsphinx',
    'sphinx.ext.mathjax',
]

master_doc = 'index'

project = 'Jupyter Notebook Tools for Sphinx'
author = 'Matthias Geier'
copyright = '2015, ' + author

# Get version information from Git:
try:
    release = check_output(['git', 'describe', '--tags', '--always'])
    release = release.decode().strip()
except Exception:
    release = '<unknown>'

# Exclude Jupyter backup files:
exclude_patterns = ['**.ipynb_checkpoints']

# -- Options for HTML output ----------------------------------------------

html_title = project + ' version ' + release

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
}

latex_documents = [
    (master_doc, 'nbsphinx.tex', project, author, 'howto'),
]
