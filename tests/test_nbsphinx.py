import sys
sys.path = ['..'] + sys.path
from nbsphinx import NotebookParser


def test_basic_parse():
    n = NotebookParser()
    n.parse('Basic.ipynb', 'basic.rst')

if __name__ == "__main__":
    test_basic_parse()
