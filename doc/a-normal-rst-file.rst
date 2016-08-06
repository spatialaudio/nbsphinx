Normal reStructuredText Files
=============================

This is a normal RST file.

.. note:: Those still work!

Links to Notebooks
------------------

Links to notebooks can be easily created:
:ref:`subdir/a-notebook-in-a-subdir.ipynb`
(the notebook title is used as link text).
You can also use
:ref:`an alternative text <subdir/a-notebook-in-a-subdir.ipynb>`.

The above links were created with:

.. code-block:: rst

    :ref:`subdir/a-notebook-in-a-subdir.ipynb`
    :ref:`an alternative text <subdir/a-notebook-in-a-subdir.ipynb>`

Links to subsections are also possible, e.g.
:ref:`subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section`
(the subsection title is used as link text) and
:ref:`alternative text <subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section>`.

These links were created with:

.. code-block:: rst

    :ref:`subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section`
    :ref:`alternative text <subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section>`

.. note::

    * Spaces in the section title have to be replaced by hyphens!
    * "``../``" is not allowed, you have to specify the full path even if the
      current source file is in a subdirectory!

Sphinx Directives for Info/Warning Boxes
----------------------------------------

.. nbwarning::
    **Warning:**

    This is an experimental feature!
    Its usage may change in the future or it might disappear completely, so
    don't use it for now.

With a bit of luck, it will be possible (some time in the future) to create
info/warning boxes in Markdown cells, see
https://github.com/jupyter/notebook/issues/1292.
If this ever happens, ``nbsphinx`` will provide directives for creating such
boxes.
For now, there are two directives available: ``nbinfo`` and ``nbwarning``.
This is how an info box looks like:

.. nbinfo::
    **Note:**

    This is an info box.

    It may include nested formatting, even another info/warning box:

    .. nbwarning:: **Warning:** You should probably not use nested boxes!
