Normal reStructuredText Files
=============================

This is a normal RST file.

.. note:: Those still work!

Links to Notebooks (and Other Sphinx Source Files)
--------------------------------------------------

Links to Sphinx source files can be created like normal `Sphinx hyperlinks`_,
just using a relative path to the local file: link_.

.. _Sphinx hyperlinks: https://www.sphinx-doc.org/en/master/usage/
                       restructuredtext/basics.html#external-links
.. _link: subdir/a-notebook-in-a-subdir.ipynb

.. code-block:: rst

    using a relative path to the local file: link_.

    .. _link: subdir/a-notebook-in-a-subdir.ipynb

If the link text has a space (or some other strange character) in it, you have
to surround it with backticks: `a notebook link`_.

.. _a notebook link: subdir/a-notebook-in-a-subdir.ipynb

.. code-block:: rst

    surround it with backticks: `a notebook link`_.

    .. _a notebook link: subdir/a-notebook-in-a-subdir.ipynb

You can also use an `anonymous hyperlink target`_, like this: link__.
If you have multiple of those, their order matters!

.. _anonymous hyperlink target: https://docutils.sourceforge.io/docs/ref/rst/
                                restructuredtext.html#anonymous-hyperlinks

__ subdir/a-notebook-in-a-subdir.ipynb

.. code-block:: rst

    like this: link__.

    __ subdir/a-notebook-in-a-subdir.ipynb

Finally, you can use `Embedded URIs`_, like this
`link <subdir/a-notebook-in-a-subdir.ipynb>`_.

.. _Embedded URIs: https://docutils.sourceforge.io/docs/ref/rst/
                   restructuredtext.html#embedded-uris-and-aliases

.. code-block:: rst

    like this `link <subdir/a-notebook-in-a-subdir.ipynb>`_.

.. note::

    These links should also work on Github and in other rendered
    reStructuredText pages.

Links to subsections are also possible by adding a hash sign (``#``) and the
section title to any of the above-mentioned link variants.
You have to replace spaces in the section titles by hyphens.
For example, see this subsection_.

.. _subsection: subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section

.. code-block:: rst

    For example, see this subsection_.

    .. _subsection: subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section


Links to Notebooks, Ye Olde Way
-------------------------------

In addition to the way shown above, you can also create links to notebooks (and
other Sphinx source files) with
`:ref: <https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#role-ref>`_.
This has some disadvantages:

* It is arguably a bit more clunky.
* Because ``:ref:`` is a Sphinx feature, the links don't work on Github and
  other rendered reStructuredText pages that use plain old ``docutils``.

It also has one important advantage:

* The link text can automatically be taken from the actual section title.

A link with automatic title looks like this:
:ref:`/subdir/a-notebook-in-a-subdir.ipynb`.

.. code-block:: rst

    :ref:`/subdir/a-notebook-in-a-subdir.ipynb`

But you can also provide
:ref:`your own link title </subdir/a-notebook-in-a-subdir.ipynb>`.

.. code-block:: rst

    :ref:`your own link title </subdir/a-notebook-in-a-subdir.ipynb>`

However, if you want to use your own title, you are probably better off using
the method described above in
`Links to Notebooks (and Other Sphinx Source Files)`_.

Links to subsections are also possible, e.g.
:ref:`/subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section`
(the subsection title is used as link text) and
:ref:`alternative text </subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section>`.

These links were created with:

.. code-block:: rst

    :ref:`/subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section`
    :ref:`alternative text </subdir/a-notebook-in-a-subdir.ipynb#A-Sub-Section>`

.. note::

    * The paths have to be relative to the top source directory and they have to
      start with a slash (``/``).
    * Spaces in the section title have to be replaced by hyphens!

Sphinx Directives for Info/Warning Boxes
----------------------------------------

.. nbwarning::
    Warning

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
    Note

    This is an info box.

    It may include nested formatting, even another info/warning box:

    .. nbwarning:: **Warning:** You should probably not use nested boxes!

Domain Objects
--------------

.. py:function:: example_python_function(foo)

    This is just for testing domain object links.

    :param str foo: Example string parameter

    .. seealso::

        :ref:`/markdown-cells.ipynb#Links-to-Domain-Objects`


References
----------

There are different ways of handling references, for example you could use the
`standard Sphinx citations`_, but it might be more practical to use the
sphinxcontrib.bibtex_ extension.

After installing the sphinxcontrib.bibtex_ extension, you have to enable it in
your ``conf.py`` and select the BibTeX file(s) you want to use:

.. code-block:: python

    extensions = [
        'nbsphinx',
        'sphinxcontrib.bibtex',
        # Probably more extensions here ...
    ]

    bibtex_bibfiles = ['my-references.bib']

Afterwards all the references defined in the bibliography file(s) can be used
throughout the Jupyter notebooks and other source files as detailed in the following.

.. _standard Sphinx Citations: https://www.sphinx-doc.org/en/master/usage/
    restructuredtext/basics.html#citations
.. _sphinxcontrib.bibtex: https://sphinxcontrib-bibtex.readthedocs.io/

Citations
^^^^^^^^^

You can create citations like :cite:`perez2011python`:

.. code-block:: rst

    :cite:`perez2011python`

You can create similar citations in Jupyter notebooks with a special HTML
syntax, see the section about
`citations in Markdown cells <markdown-cells.ipynb#Citations>`__.

You can create a list of references in any reStructuredText file
(or `reST cell <raw-cells.ipynb#reST>`_ in a notebook) like this:

.. code-block:: rst

    .. bibliography::

Have a look at the documentation for all the available options.

The list of references may look something like this (in HTML output):

.. bibliography::
    :style: alpha

However, in the LaTeX/PDF output the list of references will not appear here,
but at the end of the document.
For a possible work-around,
see https://github.com/mcmtroffaes/sphinxcontrib-bibtex/issues/156.

Footnote citations
^^^^^^^^^^^^^^^^^^

With a sphinxcontrib.bibtex_ version of ``>= 2.0.0`` it is
possible to create footnote bibliographies with footnote
citations like :footcite:`perez2011python`.

.. code-block:: rst

    :footcite:`perez2011python`

Also footnote citations can be used within Jupyter notebooks with a special HTML syntax,
see the section about
`footnote citations in Markdown cells <markdown-cells.ipynb#Footnote-citations>`__.
Footnote citations are restricted to their own source file and the assembly of the
bibliography is (analogously to normal citations) invoked with the

.. code-block:: rst

    .. footbibliography::

directive. For example, a footnote bibliography might
look like this (in HTML output):

.. footbibliography::

In the LaTeX/PDF output, there is no list of references appearing right
here. Instead, the footnote citations are placed into the footnotes of
their respective pages.


Thumbnail Galleries
-------------------

With ``nbsphinx`` you can create thumbnail galleries in notebook files
as described in :ref:`/subdir/gallery.ipynb`.

If you like, you can also create such galleries in reST files
using the ``nbgallery`` directive.

It takes the same parameters as the `toctree`__ directive.

__ https://www.sphinx-doc.org/en/master/usage/restructuredtext/
    directives.html#directive-toctree

.. note::

    The notes regarding LaTeX in :ref:`/subdir/gallery.ipynb`
    and :ref:`/subdir/toctree.ipynb` also apply here!

The following example gallery was created using:

.. code-block:: rest

    .. nbgallery::
        :caption: This is a thumbnail gallery:
        :name: rst-gallery
        :glob:
        :reversed:

        gallery/*-rst

.. nbgallery::
    :caption: This is a thumbnail gallery:
    :name: rst-gallery
    :glob:
    :reversed:

    gallery/*-rst
