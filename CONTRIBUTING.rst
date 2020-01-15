Contributing
============

If you find bugs, errors, omissions or other things that need improvement,
please create an issue or a pull request at
http://github.com/spatialaudio/nbsphinx/.
Contributions are always welcome!

Instead of pip-installing the latest release from PyPI_, you should get the
newest development version (a.k.a. "master") from Github_::

   git clone https://github.com/spatialaudio/nbsphinx.git
   cd nbsphinx
   python3 -m pip install -e . --user

This way, your installation always stays up-to-date, even if you pull new
changes from the Github repository.  If you have only Python 3 installed, you
might have to use the command ``python`` instead of ``python3``.
When installing ``nbsphinx`` this way, you can also quickly check other Git
branches (in this example the branch is called "another-branch")::

   git checkout another-branch

When you run Sphinx now, it automatically uses the version "another-branch" of
``nbsphinx``.  If you want to go back to the "master" branch, use::

   git checkout master

To get the latest changes from Github, use::

   git pull --ff-only

If you make changes to the documentation, you should create the HTML
pages locally using Sphinx and check if they look OK::

   python3 setup.py build_sphinx

To check the LaTeX output, use::

   python3 setup.py build_sphinx -b latex

Again, you'll probably have to use ``python`` instead of ``python3``.
The generated files will be available in the directories ``build/sphinx/html/``
and ``build/sphinx/latex/``, respectively.

Building Themes
---------------

The ``nbsphinx`` documentation is available in over 30 different `HTML themes`_,
with each having it's own branch ending in ``-theme``.

To simplify the building and testing of themes,
which is especially needed when changing CSS,
we provide you with command line tool to build all themes
or a user specified subset.
The tool is located at ``dev_utils/theme_builder.py`` can be run with::

    python3 dev_utils/theme_builder.py

On its first run, it will just create ``dev_utils/requirements_themes.txt``
which contains the dependencies to build to build all themes and instructs
you how to install them.
And after it will by default build all supported themes.

If you just want to build a subset of the themes
(i.e. ``alabaster`` and ``sphinx_rtd_theme``), simply run::

    python3 dev_utils/theme_builder.py --themes alabaster rtd

for more information run::

    python3 dev_utils/theme_builder.py --help

.. _PyPI: https://pypi.org/project/nbsphinx/
.. _Github: https://github.com/spatialaudio/nbsphinx/
.. _`HTML themes`: https://nbsphinx.readthedocs.io/en/0.5.0/usage.html#HTML-Themes
