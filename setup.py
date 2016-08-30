from setuptools import setup

# "import" __version__
for line in open("nbsphinx.py"):
    if line.startswith("__version__"):
        exec(line)
        break

setup(
    name='nbsphinx',
    version=__version__,
    py_modules=['nbsphinx'],
    install_requires=[
        'docutils',
        'jinja2',
        'nbconvert',
        'traitlets',
        'nbformat',
        'sphinx',
    ],
    author='Matthias Geier',
    author_email='Matthias.Geier@gmail.com',
    description='Jupyter Notebook Tools for Sphinx',
    long_description=open('README.rst').read(),
    license='MIT',
    keywords='Sphinx Jupyter notebook'.split(),
    url='http://nbsphinx.rtfd.org/',
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Sphinx',
        'Framework :: Sphinx :: Extension',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Documentation :: Sphinx',
    ],
    zip_safe=True,
)
