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
   python setup.py develop --user

This way, your installation always stays up-to-date, even if you pull new
changes from the Github repository.  If you have both Python 2 and 3 installed,
you might have to use the command ``python3`` instead of ``python``.
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

   python setup.py build_sphinx

To check the LaTeX output, use::

   python setup.py build_sphinx -b latex

Again, you'll probably have to use ``python3`` instead of ``python``.
The generated files will be available in the directories ``build/sphinx/html/``
and ``build/sphinx/latex/``, respectively.

.. _PyPI: https://pypi.python.org/pypi/nbsphinx/
.. _Github: http://github.com/spatialaudio/nbsphinx/
