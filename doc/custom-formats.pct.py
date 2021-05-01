# %% [markdown]
# # Custom Notebook Formats
#
# By default, Jupyter notebooks are stored in files with the suffix `.ipynb`,
# which use the JSON format for storage.
#
# However, there are libraries available which allow storing notebooks
# in different formats, using different file suffixes.
#
# To use a custom notebook format in `nbsphinx`, you can specify the
# `nbsphinx_custom_formats` option in your `conf.py` file.
# You have to provide the file extension
# and a conversion function that takes the contents of a file (as a string)
# and returns a Jupyter notebook object.
#
# ```python
# nbsphinx_custom_formats = {
#     '.mysuffix': 'mylibrary.converter_function',
# }
# ```
#
# The converter function can be given as a string (recommended)
# or as a function object.
#
# If a conversion function takes more than a single string argument,
# you can specify the function name plus a dictionary with keyword arguments
# which will be passed to the conversion function in addition to the
# file contents.
#
# ```python
# nbsphinx_custom_formats = {
#     '.mysuffix': ['mylibrary.converter_function', {'some_arg': 42}],
# }
# ```
#
# You can of course use multiple formats
# by specifying multiple conversion functions.

# %% [markdown]
# ## Example: Jupytext
#
# One example for a library which provides a custom conversion function is
# [jupytext](https://github.com/mwouts/jupytext),
# which allows storing the contents of Jupyter notebooks in
# Markdown and R-Markdown, as well as plain Julia, Python and R files.
#
# Since its conversion function takes more than a single string argument,
# we have to pass a keyword argument, e.g.:
#
# ```python
# nbsphinx_custom_formats = {
#     '.Rmd': ['jupytext.reads', {'fmt': 'Rmd'}],
# }
# ```

# %% [markdown]
# This very page is an example of a notebook stored in the
# `py:percent` format
# (see [docs](https://jupytext.readthedocs.io/en/latest/formats.html#the-percent-format)):

# %%
# !head -20 custom-formats.pct.py

# %% [raw] raw_mimetype="text/restructuredtext"
# To select a suitable conversion function,
# we use the following setting in :download:`conf.py`:
#
# .. literalinclude:: conf.py
#     :language: python
#     :start-at: nbsphinx_custom_formats
#     :lines: -4
#     :emphasize-lines: 2

# %% [markdown]
# Another example is [this gallery example page](gallery/due-rst.pct.py).
