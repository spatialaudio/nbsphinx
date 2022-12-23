Including Sphinx-Generated Content in a LaTeX Document
======================================================

This sub-directory is an example for how a Sphinx-based project
(in this case the `nbsphinx` documentation)
can be included as part or chapter of a larger,
otherwise hand-written LaTeX document
(in this case [my-latex-document.tex][]).

This technique is not specific to `nbsphinx`, except for this one line:

    \usepackage{nbsphinx}

If you want to use it without `nbsphinx`, just remove this line.

The main idea of this setup is that Sphinx is called with
the original source directory `../doc`
but specifying this directory
(which contains another [conf.py][] overriding some of the original settings)
as configuration directory (with `-c .`):

    python -m sphinx ../doc _build -c . -b latex

Note that even though Sphinx suggests that in its console messages,
running LaTeX in the `_build` directory will *not* work,
because the `.tex` file in there is not a stand-alone LaTeX document
(it is based on a [minimalistic template][]).
It is meant to be included in the file [my-latex-document.tex][]
in this directory, so LaTeX has to be called from here:

    latexmk -pv

The configuration file [latexmkrc][] manipulates the environment variable
`TEXINPUTS` so that LaTeX can find all necessary files.

[my-latex-document.tex]: my-latex-document.tex
[conf.py]: conf.py
[minimalistic template]: _templates/latex.tex_t
[latexmkrc]: latexmkrc
