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

# *** the following lines are (hopefully) temporary,
# see https://github.com/sphinx-doc/sphinx/issues/2162
import nbsphinx
source_suffix = ['.rst', '.ipynb']
source_parsers = {'ipynb': nbsphinx.NotebookParser}
# *** end of temporary lines

master_doc = 'index'

project = 'nbsphinx'
author = 'Matthias Geier'
copyright = '2015, ' + author

# Get version information from Git:
try:
    release = check_output(['git', 'describe', '--tags', '--always'])
    release = release.decode().strip()
except Exception:
    release = '<unknown>'

# Exclude build directory and Jupyter backup files:
exclude_patterns = ['_build', '**.ipynb_checkpoints']

# -- Options for HTML output ----------------------------------------------

html_title = project + ' version ' + release

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
}

latex_documents = [
    (master_doc, 'nbsphinx.tex', project, author, 'howto'),
]
