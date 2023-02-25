References
==========

By default, in the LaTeX/PDF output the list of references will not appear here,
but instead at the end of the document.
For a possible work-around (which is also used here)
see https://github.com/mcmtroffaes/sphinxcontrib-bibtex/issues/156.

The list of references may look something like this:

.. raw:: latex

    \begingroup
    \def\section#1#2{}
    \def\chapter#1#2{}
    \begin{thebibliography}{1234}

.. bibliography::
    :style: alpha

.. raw:: latex

    \end{thebibliography}
    \endgroup

.. warning::

    With ``docutils`` versions 0.18 and 0.19,
    the HTML output after the bibliography is broken,
    see https://github.com/mcmtroffaes/sphinxcontrib-bibtex/issues/309.
    This problem will be fixed in the next ``docutils`` version
    (either 0.19.1 or 0.20).
