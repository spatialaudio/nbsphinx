A Normal reStructuredText File
==============================

This is a normal RST file.

.. note:: Those still work!

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
