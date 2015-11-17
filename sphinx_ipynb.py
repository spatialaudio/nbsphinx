"""Sphinx source parser for ipynb files."""
import docutils
import nbconvert
import nbformat

_ipynbversion = 4


class NotebookParser(docutils.parsers.rst.Parser):

    def parse(self, inputstring, document):
        nb = nbformat.reads(inputstring, as_version=_ipynbversion)

        # TODO: check if outputs are available and execute notebook if not
        # TODO: save a copy of the notebook with and without outputs
        #       (see "source" of document)

        exporter = nbconvert.RSTExporter()
        rststring, resources = exporter.from_notebook_node(nb)

        docutils.parsers.rst.Parser.parse(self, rststring, document)
