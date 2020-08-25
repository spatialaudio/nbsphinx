Contributing
============

If you find bugs, errors, omissions or other things that need improvement,
please create an issue or a pull request at
https://github.com/spatialaudio/nbsphinx/.
Contributions are always welcome!


Development Installation
------------------------

Instead of pip-installing the latest release from PyPI_, you should get the
newest development version (a.k.a. "master") with Git::

   git clone https://github.com/spatialaudio/nbsphinx.git
   cd nbsphinx
   python3 -m pip install -e . --user

... where ``-e`` stands for ``--editable``.

When installing this way, you can quickly try other Git
branches (in this example the branch is called "another-branch")::

   git checkout another-branch

If you want to go back to the "master" branch, use::

   git checkout master

To get the latest changes from Github, use::

   git pull --ff-only


Building the Documentation
--------------------------

If you make changes to the documentation, you should create the HTML
pages locally using Sphinx and check if they look OK.

Initially, you might need to install a few packages that are needed to build the
documentation::

   python3 -m pip install -r doc/requirements.txt --user

To (re-)build the HTML files, use::

   python3 setup.py build_sphinx

If you want to check the LaTeX output, use::

   python3 setup.py build_sphinx -b latex

Again, you'll probably have to use ``python`` instead of ``python3``.
The generated files will be available in the directories ``build/sphinx/html/``
and ``build/sphinx/latex/``, respectively.

.. _PyPI: https://pypi.org/project/nbsphinx/


Testing
-------

Unfortunately, the currently available automated tests are very limited.
Contributions to improve the testing situation are of course also welcome!

The ``nbsphinx`` documentation also serves as a test case.
However, the resulting HTML/LaTeX/PDF files have to be inspected manually to
check whether they look as expected.

Sphinx's warnings can help spot problems, therefore it is recommended to use the
``-W`` flag to turn Sphinx warnings into errors while testing::

   python3 setup.py build_sphinx -W

This flag is also used for continuous integration on
Travis-CI (see the file ``.travis.yml``) and
CircleCI (see the file ``.circleci/config.yml``).

Sphinx has a ``linkcheck`` builder that can check whether all URLs used in the
documentation are still valid.
This is also part of the continuous integration setup on CircelCI.
