Contributing
============

If you find bugs, errors, omissions or other things that need improvement,
please create an issue or a pull request at
http://github.com/spatialaudio/nbsphinx/.
Contributions are always welcome!


Development Installation
------------------------

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
.. _Github: https://github.com/spatialaudio/nbsphinx/


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
