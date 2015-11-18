"""Sphinx source parser for ipynb files."""
import docutils
import nbconvert
import nbformat

_ipynbversion = 4


class NotebookParser(docutils.parsers.rst.Parser):

    def parse(self, inputstring, document):
        nb = nbformat.reads(inputstring, as_version=_ipynbversion)

        resources = {}

        # Execute notebook only if there are no outputs:
        if not any(c.outputs for c in nb.cells if 'outputs' in c):
            pp = nbconvert.preprocessors.ExecutePreprocessor()
            nb, resources = pp.preprocess(nb, resources)

        # TODO: save a copy of the notebook with and without outputs
        #       (see "source" of document)

        exporter = nbconvert.RSTExporter()
        rststring, resources = exporter.from_notebook_node(nb)

        docutils.parsers.rst.Parser.parse(self, rststring, document)
