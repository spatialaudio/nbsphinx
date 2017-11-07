from setuptools import setup

# "import" __version__
__version__ = 'unknown'
for line in open('src/nbsphinx.py'):
    if line.startswith('__version__'):
        exec(line)
        break

setup(
    name='nbsphinx',
    version=__version__,
    package_dir={'': 'src'},
    py_modules=['nbsphinx'],
    install_requires=[
        'docutils',
        'jinja2',
        'nbconvert',
        'traitlets',
        'nbformat',
        'sphinx>=1.3.2,!=1.5.0',
    ],
    author='Matthias Geier',
    author_email='Matthias.Geier@gmail.com',
    description='Jupyter Notebook Tools for Sphinx',
    long_description=open('README.rst').read(),
    license='MIT',
    keywords='Sphinx Jupyter notebook'.split(),
    url='http://nbsphinx.readthedocs.io/',
    platforms='any',
    classifiers=[
        'Framework :: Sphinx',
        'Framework :: Sphinx :: Extension',
        'Framework :: Jupyter',
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
