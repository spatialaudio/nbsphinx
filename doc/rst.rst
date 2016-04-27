A Normal reStructuredText File
==============================

This is a normal RST file.

.. note:: Those still work!

Links to Notebooks
------------------

Links to notebooks can be easily created: :ref:`subdir/another.ipynb` (the
notebook title is used as link text).
You can also use :ref:`an alternative text <subdir/another.ipynb>`.

The above links were created with:

.. code-block:: rst

    :ref:`subdir/another.ipynb`
    :ref:`an alternative text <subdir/another.ipynb>`

Links to subsections are also possible,
e.g.  :ref:`subdir/another.ipynb#A-Sub-Section` (the subsection title is used
as link text) and :ref:`alternative text <subdir/another.ipynb#A-Sub-Section>`.

These links were created with:

.. code-block:: rst

    :ref:`subdir/another.ipynb#A-Sub-Section`
    :ref:`alternative text <subdir/another.ipynb#A-Sub-Section>`

.. note::

    * Spaces in the section title have to be replaced by hyphens!
    * "``../``" is not allowed, you have to specify the full path even if the
      current source file is in a subdirectory!

Sphinx Directives for Jupyter Notebook Cells
--------------------------------------------

For comparison, this is a "normal" Sphinx code block using ``ipython3``
syntax highlighting:

.. code-block:: ipython3

    %file helloworld.py
    #!/usr/bin/env python3
    print('Hello, world!')

The ``nbsphinx`` extension provides custom directives to show notebook cells:

.. nbinput:: ipython3
    :execution-count: 42

    6 * 7

.. nboutput::
    :execution-count: 42

    42

This was created with

.. code-block:: rst

    .. nbinput:: ipython3
        :execution-count: 42

        6 * 7

    .. nboutput::
        :execution-count: 42

        42

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
