#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Use sphinx-quickstart to create your own conf.py file!
# After that, you have to edit a few things.  See below.

import sys
import os
from subprocess import check_output

# Add path to nbsphinx.py (if you didn't install it with pip):
sys.path.insert(0, os.path.abspath('..'))

# If you copied the file to the current directory, use this instead:
#sys.path.insert(0, os.path.abspath('.'))

from nbsphinx import NotebookParser

# If needed, select a math extensions (mathjax or pngmath):
extensions = [
    'sphinx.ext.mathjax',
]

# This allows Jupyter notebooks as sources (besides reStructuredText):
source_suffix = ['.rst', '.ipynb']
source_parsers = {'ipynb': NotebookParser}

master_doc = 'index'

project = 'Jupyter Notebook Tools for Sphinx'
author = 'Matthias Geier'
copyright = '2015, ' + author

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
