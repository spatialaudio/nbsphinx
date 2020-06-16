Version 0.7.1 (2020-06-16):
 * Avoid links on scaled images

Version 0.7.0 (2020-05-08):
 * Warnings can be suppressed with ``suppress_warnings``.
 * ``<img>`` tags are handled in Markdown cells; the ``alt``, ``width``,
   ``height`` and ``class`` attributes are supported.
 * CSS: prompts protrude into left margin if ``nbsphinx_prompt_width`` is
   too small. If you want to hide the prompts, use `custom CSS`__.

   __ https://nbsphinx.readthedocs.io/en/0.7.0/custom-css.html
Version 0.6.1 (2020-04-18):
 * ``.ipynb_checkpoints`` is automatically added to ``exclude_patterns``

Version 0.6.0 (2020-04-03):
 * Thumbnail galleries (inspired by https://sphinx-gallery.github.io/)
 * ``nbsphinx-toctree`` as cell tag
 * Keyword arguments in ``nbsphinx_custom_formats``
 * Python 2 support has been dropped

Version 0.5.1 (2020-01-28):
 * This will be the last release supporting Python 2.x!
 * Support for https://github.com/choldgraf/sphinx-copybutton
 * Executed notebooks are now saved in the HTML output directory

Version 0.5.0 (2019-11-20):
 * Automatic support for Jupyter widgets, customizable with
   ``nbsphinx_widgets_path`` (and ``nbsphinx_widgets_options``)

Version 0.4.3 (2019-09-30):
 * Add option ``nbsphinx_requirejs_path`` (and ``nbsphinx_requirejs_options``)

Version 0.4.2 (2019-01-15):
 * Re-establish Python 2 compatibility (but the clock is ticking ...)

Version 0.4.1 (2018-12-16):
 * Fix issue #266

Version 0.4.0 (2018-12-14):
 * Support for "data-cite" HTML tags in Markdown cells
 * Add option ``nbsphinx_custom_formats``
 * LaTeX macros ``\nbsphinxstartnotebook`` and ``\nbsphinxstopnotebook``
 * Support for cell attachments
 * Add options ``nbsphinx_input_prompt`` and ``nbsphinx_output_prompt``
 * Re-design LaTeX output of code cells, fix image sizes

Version 0.3.5 (2018-09-10):
 * Disable ``nbconvert`` version 5.4 to avoid
   `issue #878 <https://github.com/jupyter/nbconvert/issues/878>`__

Version 0.3.4 (2018-07-28):
 * Fix issue #196 and other minor changes

Version 0.3.3 (2018-04-25):
 * Locally linked files are only copied for Jupyter notebooks (and not anymore
   for other Sphinx source files)

Version 0.3.2 (2018-03-28):
 * Links to local files are rewritten for all Sphinx source files (not only
   Jupyter notebooks)

Version 0.3.1 (2018-01-17):
 * Enable notebook translations (NB: The use of reST strings is temporary!)

Version 0.3.0 (2018-01-02):
 * Add options ``nbsphinx_prolog`` and ``nbsphinx_epilog``
 * Links from ``*.rst`` files to notebooks have to start with a slash

Version 0.2.18 (2017-12-03):
 * Fix issue #148

Version 0.2.17 (2017-11-12):
 * Fix issue #146

Version 0.2.16 (2017-11-07):
 * Fix issue #142

Version 0.2.15 (2017-11-03):
 * Links to subsections are now possible in all source files

Version 0.2.14 (2017-06-09):
 * Add option ``nbsphinx_kernel_name``

Version 0.2.13 (2017-01-25):
 * Minor fixes

Version 0.2.12 (2016-12-19):
 * Basic support for widgets
 * CSS is now "responsive", some new CSS classes

Version 0.2.11 (2016-11-19):
 * Minor fixes

Version 0.2.10 (2016-10-16):
 * Enable JavaScript output cells

Version 0.2.9 (2016-07-26):
 * Add option ``nbsphinx_prompt_width``

Version 0.2.8 (2016-05-20):
 * Add options ``nbsphinx_execute`` and ``nbsphinx_execute_arguments``
 * Separate "display priority" for HTML and LaTeX

Version 0.2.7 (2016-05-04):
 * Special CSS tuning for ``sphinx_rtd_theme``
 * Replace info/warning ``<div>`` elements with ``nbinfo``/``nbwarning``

Version 0.2.6 (2016-04-12):
 * Support for LaTeX math environments in Markdown cells
 * Add options ``nbsphinx_timeout`` and ``nbsphinx_codecell_lexer``

Version 0.2.5 (2016-03-15):
 * Add option ``nbsphinx_allow_errors`` to globally ignore exceptions
 * Separate class `nbsphinx.Exporter`

Version 0.2.4 (2016-02-12):
 * Support for "nbsphinx-toctree" cell metadata

Version 0.2.3 (2016-01-22):
 * Links from notebooks to local files can now be used

Version 0.2.2 (2016-01-06):
 * Support for links to sub-sections in other notebooks

Version 0.2.1 (2016-01-04):
 * No need to mention ``source_suffix`` and ``source_parsers`` in ``conf.py``

Version 0.2.0 (2015-12-27):
 * Add support for ``allow_errors`` and ``hidden`` metadata
 * Add custom reST template
 * Add nbinput and nboutput directives with HTML+CSS and LaTeX formatting
 * Turn nbsphinx into a Sphinx extension

Version 0.1.0 (2015-11-29):
   Initial release
