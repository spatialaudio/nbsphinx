# %% [markdown]
# # Dummy Notebook 2 for Gallery
#
# This is a dummy file just to fill
# [the gallery in the reST file](../a-normal-rst-file.rst#thumbnail-galleries).
#
# The thumbnail image is assigned in [conf.py](../conf.py).

# %% [markdown]
# The source file is, for no particular reason,
# a Python script adhering to the `py:percent` format.
# It is parsed with the help of [Jupytext](https://jupytext.readthedocs.io/),
# see [Custom Notebook Formats](../custom-formats.ipynb).

# %%
from pathlib import Path

# %%
filename = 'due-rst.pct.py'

print(Path(filename).read_text())
