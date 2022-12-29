Version 0.8.11 -- 2022-12-29 -- PyPI__ -- diff__
 * LaTeX: apply code cell border style to all code blocks

__ https://pypi.org/project/nbsphinx/0.8.11/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.10...0.8.11

Version 0.8.10 -- 2022-11-13 -- PyPI__ -- diff__
 * Fix handling of ``source_suffix``
 * A few LaTeX fixes

__ https://pypi.org/project/nbsphinx/0.8.10/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.9...0.8.10

Version 0.8.9 -- 2022-06-04 -- PyPI__ -- diff__
 * CSS: support tables in widgets
 * Avoid empty "raw" directive

__ https://pypi.org/project/nbsphinx/0.8.9/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.8...0.8.9

Version 0.8.8 -- 2021-12-31 -- PyPI__ -- diff__
 * Support for the ``sphinx_codeautolink`` extension
 * Basic support for the ``text`` builder

__ https://pypi.org/project/nbsphinx/0.8.8/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.7...0.8.8

Version 0.8.7 -- 2021-08-10 -- PyPI__ -- diff__
 * Fix assertion error in LaTeX build with Sphinx 4.1.0+

__ https://pypi.org/project/nbsphinx/0.8.7/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.6...0.8.7

Version 0.8.6 -- 2021-06-03 -- PyPI__ -- diff__
 * Support for Jinja2 version 3

__ https://pypi.org/project/nbsphinx/0.8.6/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.5...0.8.6

Version 0.8.5 -- 2021-05-12 -- PyPI__ -- diff__
 * Freeze Jinja2 version to 2.11 (for now, until a bugfix is found)
 * Add ``theme_comparison.py`` tool for creating multiple versions
   (with different HTML themes) of the docs at once

__ https://pypi.org/project/nbsphinx/0.8.5/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.4...0.8.5

Version 0.8.4 -- 2021-04-29 -- PyPI__ -- diff__
 * Support for ``mathjax3_config`` (for Sphinx >= 4)
 * Force loading MathJax on HTML pages generated from notebooks
   (can be disabled with ``nbsphinx_assume_equations = False``)

__ https://pypi.org/project/nbsphinx/0.8.4/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.3...0.8.4

Version 0.8.3 -- 2021-04-09 -- PyPI__ -- diff__
 * Increase ``line_length_limit`` (for `docutils` 0.17+)

__ https://pypi.org/project/nbsphinx/0.8.3/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.2...0.8.3

Version 0.8.2 -- 2021-02-28 -- PyPI__ -- diff__
 * Add support for ``data-footcite`` HTML attribute
 * Disable automatic highlighting in notebooks,
   setting ``highlight_language`` is no longer needed

__ https://pypi.org/project/nbsphinx/0.8.2/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.1...0.8.2

Version 0.8.1 -- 2021-01-18 -- PyPI__ -- diff__
 * Minor fixes and documentation update

__ https://pypi.org/project/nbsphinx/0.8.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.8.0...0.8.1

Version 0.8.0 -- 2020-10-20 -- PyPI__ -- diff__
 * Don't overwrite Pygments background in notebook code cells.
   To get rid of those ugly greenish code blocks,
   remove ``pygments_style = 'sphinx'`` from your ``conf.py``.
 * Switch documentation to
   `insipid <https://insipid-sphinx-theme.readthedocs.io/>`_ theme by default
 * Require Python 3.6+

__ https://pypi.org/project/nbsphinx/0.8.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.7.1...0.8.0

Version 0.7.1 -- 2020-06-16 -- PyPI__ -- diff__
 * Avoid links on scaled images

__ https://pypi.org/project/nbsphinx/0.7.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.7.0...0.7.1

Version 0.7.0 -- 2020-05-08 -- PyPI__ -- diff__
 * Warnings can be suppressed with ``suppress_warnings``.
 * ``<img>`` tags are handled in Markdown cells; the ``alt``, ``width``,
   ``height`` and ``class`` attributes are supported.
 * CSS: prompts protrude into left margin if ``nbsphinx_prompt_width`` is
   too small. If you want to hide the prompts, use
   `custom CSS <https://nbsphinx.readthedocs.io/en/0.7.0/custom-css.html>`_.

__ https://pypi.org/project/nbsphinx/0.7.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.6.1...0.7.0

Version 0.6.1 -- 2020-04-18 -- PyPI__ -- diff__
 * ``.ipynb_checkpoints`` is automatically added to ``exclude_patterns``

__ https://pypi.org/project/nbsphinx/0.6.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.6.0...0.6.1

Version 0.6.0 -- 2020-04-03 -- PyPI__ -- diff__
 * Thumbnail galleries (inspired by https://sphinx-gallery.github.io/)
 * ``nbsphinx-toctree`` as cell tag
 * Keyword arguments in ``nbsphinx_custom_formats``
 * Python 2 support has been dropped

__ https://pypi.org/project/nbsphinx/0.6.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.5.1...0.6.0

Version 0.5.1 -- 2020-01-28 -- PyPI__ -- diff__
 * This will be the last release supporting Python 2.x!
 * Support for https://github.com/choldgraf/sphinx-copybutton
 * Executed notebooks are now saved in the HTML output directory

__ https://pypi.org/project/nbsphinx/0.5.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.5.0...0.5.1

Version 0.5.0 -- 2019-11-20 -- PyPI__ -- diff__
 * Automatic support for Jupyter widgets, customizable with
   ``nbsphinx_widgets_path`` (and ``nbsphinx_widgets_options``)

__ https://pypi.org/project/nbsphinx/0.5.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.4.3...0.5.0

Version 0.4.3 -- 2019-09-30 -- PyPI__ -- diff__
 * Add option ``nbsphinx_requirejs_path`` (and ``nbsphinx_requirejs_options``)

__ https://pypi.org/project/nbsphinx/0.4.3/
__ https://github.com/spatialaudio/nbsphinx/compare/0.4.2...0.4.3

Version 0.4.2 -- 2019-01-15 -- PyPI__ -- diff__
 * Re-establish Python 2 compatibility (but the clock is ticking ...)

__ https://pypi.org/project/nbsphinx/0.4.2/
__ https://github.com/spatialaudio/nbsphinx/compare/0.4.1...0.4.2

Version 0.4.1 -- 2018-12-16 -- PyPI__ -- diff__
 * Fix issue #266

__ https://pypi.org/project/nbsphinx/0.4.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.4.0...0.4.1

Version 0.4.0 -- 2018-12-14 -- PyPI__ -- diff__
 * Support for "data-cite" HTML tags in Markdown cells
 * Add option ``nbsphinx_custom_formats``
 * LaTeX macros ``\nbsphinxstartnotebook`` and ``\nbsphinxstopnotebook``
 * Support for cell attachments
 * Add options ``nbsphinx_input_prompt`` and ``nbsphinx_output_prompt``
 * Re-design LaTeX output of code cells, fix image sizes

__ https://pypi.org/project/nbsphinx/0.4.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.5...0.4.0

Version 0.3.5 -- 2018-09-10 -- PyPI__ -- diff__
 * Disable ``nbconvert`` version 5.4 to avoid
   `issue #878 <https://github.com/jupyter/nbconvert/issues/878>`__

__ https://pypi.org/project/nbsphinx/0.3.5/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.4...0.3.5

Version 0.3.4 -- 2018-07-28 -- PyPI__ -- diff__
 * Fix issue #196 and other minor changes

__ https://pypi.org/project/nbsphinx/0.3.4/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.3...0.3.4

Version 0.3.3 -- 2018-04-25 -- PyPI__ -- diff__
 * Locally linked files are only copied for Jupyter notebooks (and not anymore
   for other Sphinx source files)

__ https://pypi.org/project/nbsphinx/0.3.3/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.2...0.3.3

Version 0.3.2 -- 2018-03-28 -- PyPI__ -- diff__
 * Links to local files are rewritten for all Sphinx source files (not only
   Jupyter notebooks)

__ https://pypi.org/project/nbsphinx/0.3.2/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.1...0.3.2

Version 0.3.1 -- 2018-01-17 -- PyPI__ -- diff__
 * Enable notebook translations (NB: The use of reST strings is temporary!)

__ https://pypi.org/project/nbsphinx/0.3.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.3.0...0.3.1

Version 0.3.0 -- 2018-01-02 -- PyPI__ -- diff__
 * Add options ``nbsphinx_prolog`` and ``nbsphinx_epilog``
 * Links from ``*.rst`` files to notebooks have to start with a slash

__ https://pypi.org/project/nbsphinx/0.3.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.18...0.3.0

Version 0.2.18 -- 2017-12-03 -- PyPI__ -- diff__
 * Fix issue #148

__ https://pypi.org/project/nbsphinx/0.2.18/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.17...0.2.18

Version 0.2.17 -- 2017-11-12 -- PyPI__ -- diff__
 * Fix issue #146

__ https://pypi.org/project/nbsphinx/0.2.17/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.16...0.2.17

Version 0.2.16 -- 2017-11-07 -- PyPI__ -- diff__
 * Fix issue #142

__ https://pypi.org/project/nbsphinx/0.2.16/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.15...0.2.16

Version 0.2.15 -- 2017-11-03 -- PyPI__ -- diff__
 * Links to subsections are now possible in all source files

__ https://pypi.org/project/nbsphinx/0.2.15/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.14...0.2.15

Version 0.2.14 -- 2017-06-09 -- PyPI__ -- diff__
 * Add option ``nbsphinx_kernel_name``

__ https://pypi.org/project/nbsphinx/0.2.14/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.13...0.2.14

Version 0.2.13 -- 2017-01-25 -- PyPI__ -- diff__
 * Minor fixes

__ https://pypi.org/project/nbsphinx/0.2.13/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.12...0.2.13

Version 0.2.12 -- 2016-12-19 -- PyPI__ -- diff__
 * Basic support for widgets
 * CSS is now "responsive", some new CSS classes

__ https://pypi.org/project/nbsphinx/0.2.12/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.11...0.2.12

Version 0.2.11 -- 2016-11-19 -- PyPI__ -- diff__
 * Minor fixes

__ https://pypi.org/project/nbsphinx/0.2.11/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.10...0.2.11

Version 0.2.10 -- 2016-10-16 -- PyPI__ -- diff__
 * Enable JavaScript output cells

__ https://pypi.org/project/nbsphinx/0.2.10/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.9...0.2.10

Version 0.2.9 -- 2016-07-26 -- PyPI__ -- diff__
 * Add option ``nbsphinx_prompt_width``

__ https://pypi.org/project/nbsphinx/0.2.9/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.8...0.2.9

Version 0.2.8 -- 2016-05-20 -- PyPI__ -- diff__
 * Add options ``nbsphinx_execute`` and ``nbsphinx_execute_arguments``
 * Separate "display priority" for HTML and LaTeX

__ https://pypi.org/project/nbsphinx/0.2.8/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.7...0.2.8

Version 0.2.7 -- 2016-05-04 -- PyPI__ -- diff__
 * Special CSS tuning for ``sphinx_rtd_theme``
 * Replace info/warning ``<div>`` elements with ``nbinfo``/``nbwarning``

__ https://pypi.org/project/nbsphinx/0.2.7/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.6...0.2.7

Version 0.2.6 -- 2016-04-12 -- PyPI__ -- diff__
 * Support for LaTeX math environments in Markdown cells
 * Add options ``nbsphinx_timeout`` and ``nbsphinx_codecell_lexer``

__ https://pypi.org/project/nbsphinx/0.2.6/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.5...0.2.6

Version 0.2.5 -- 2016-03-15 -- PyPI__ -- diff__
 * Add option ``nbsphinx_allow_errors`` to globally ignore exceptions
 * Separate class `nbsphinx.Exporter`

__ https://pypi.org/project/nbsphinx/0.2.5/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.4...0.2.5

Version 0.2.4 -- 2016-02-12 -- PyPI__ -- diff__
 * Support for "nbsphinx-toctree" cell metadata

__ https://pypi.org/project/nbsphinx/0.2.4/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.3...0.2.4

Version 0.2.3 -- 2016-01-22 -- PyPI__ -- diff__
 * Links from notebooks to local files can now be used

__ https://pypi.org/project/nbsphinx/0.2.3/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.2...0.2.3

Version 0.2.2 -- 2016-01-06 -- PyPI__ -- diff__
 * Support for links to sub-sections in other notebooks

__ https://pypi.org/project/nbsphinx/0.2.2/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.1...0.2.2

Version 0.2.1 -- 2016-01-04 -- PyPI__ -- diff__
 * No need to mention ``source_suffix`` and ``source_parsers`` in ``conf.py``

__ https://pypi.org/project/nbsphinx/0.2.1/
__ https://github.com/spatialaudio/nbsphinx/compare/0.2.0...0.2.1

Version 0.2.0 -- 2015-12-27 -- PyPI__ -- diff__
 * Add support for ``allow_errors`` and ``hidden`` metadata
 * Add custom reST template
 * Add nbinput and nboutput directives with HTML+CSS and LaTeX formatting
 * Turn nbsphinx into a Sphinx extension

__ https://pypi.org/project/nbsphinx/0.2.0/
__ https://github.com/spatialaudio/nbsphinx/compare/0.1.0...0.2.0

Version 0.1.0 -- 2015-11-29
   Initial release
