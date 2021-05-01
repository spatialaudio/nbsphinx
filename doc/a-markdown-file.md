# Using Markdown Files

It is possible to use Markdown source files, as explained in the
[Sphinx documentation](https://www.sphinx-doc.org/en/master/usage/markdown.html).

The Python package ``myst-parser`` has to be installed and
``conf.py`` should at least contain this:

```python
extensions = [
    'nbsphinx',
    'myst_parser',
]

myst_update_mathjax = False
```


## Links to Notebooks (and Other Sphinx Source Files)

Links to Sphinx source files can be created like in
[Markdown cells of notebooks](markdown-cells.html#Links-to-Other-Notebooks).


## Math

Math equation can be used just like in
[Markdown cells of notebooks](markdown-cells.html#Equations).

Inline like this: $\text{e}^{i\pi} = -1$.

Or as a separate block:

\begin{equation}
\int\limits_{-\infty}^\infty f(x) \delta(x - x_0) dx = f(x_0)
\end{equation}
