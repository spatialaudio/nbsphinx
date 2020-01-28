# Copyright (c) 2015-2020 Matthias Geier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Jupyter Notebook Tools for Sphinx.

https://nbsphinx.readthedocs.io/

"""
__version__ = '0.5.1'

import copy
import json
import os
import re
import subprocess
try:
    from urllib.parse import unquote  # Python 3.x
    from html.parser import HTMLParser
except ImportError:
    from urllib2 import unquote  # Python 2.x
    from HTMLParser import HTMLParser

import docutils
from docutils.parsers import rst
import jinja2
import nbconvert
import nbformat
import sphinx
import sphinx.errors
import sphinx.transforms.post_transforms.images
import traitlets

_ipynbversion = 4

# See nbconvert/exporters/html.py:
DISPLAY_DATA_PRIORITY_HTML = (
    'application/vnd.jupyter.widget-state+json',
    'application/vnd.jupyter.widget-view+json',
    'application/javascript',
    'text/html',
    'text/markdown',
    'image/svg+xml',
    'text/latex',
    'image/png',
    'image/jpeg',
    'text/plain',
)
# See nbconvert/exporters/latex.py:
DISPLAY_DATA_PRIORITY_LATEX = (
    'text/latex',
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/svg+xml',
    'text/markdown',
    'text/plain',
)

# The default rst template name is changing in nbconvert 6, so we substitute
# it in to the *extends* directive.
RST_TEMPLATE = """
{% extends '__RST_DEFAULT_TEMPLATE__' %}

{% macro insert_empty_lines(text) %}
{%- set before, after = text | get_empty_lines %}
{%- if before %}
    :empty-lines-before: {{ before }}
{%- endif %}
{%- if after %}
    :empty-lines-after: {{ after }}
{%- endif %}
{%- endmacro %}


{% block any_cell %}
{%- if cell.metadata.nbsphinx != 'hidden' %}
{{ super() }}
{% endif %}
{%- endblock any_cell %}


{% block input -%}
.. nbinput:: {% if cell.metadata.magics_language -%}
{{ cell.metadata.magics_language }}
{%- elif nb.metadata.language_info -%}
{{ nb.metadata.language_info.pygments_lexer or nb.metadata.language_info.name }}
{%- else -%}
{{ resources.codecell_lexer }}
{%- endif -%}
{{ insert_empty_lines(cell.source) }}
{%- if cell.execution_count %}
    :execution-count: {{ cell.execution_count }}
{%- endif %}
{%- if not cell.outputs %}
    :no-output:
{%- endif %}

{{ cell.source.strip('\n') | indent }}
{% endblock input %}


{% macro insert_nboutput(datatype, output, cell) -%}
.. nboutput::
{%- if output.output_type == 'execute_result' and cell.execution_count %}
    :execution-count: {{ cell.execution_count }}
{%- endif %}
{%- if output != cell.outputs[-1] %}
    :more-to-come:
{%- endif %}
{%- if output.name == 'stderr' %}
    :class: stderr
{%- endif %}
{%- if datatype != 'text/plain' %}
    :fancy:
{%- endif %}
{%- if datatype == 'text/plain' %}

    .. rst-class:: highlight

    .. raw:: html

        <pre>
{{ output.data[datatype] | ansi2html | indent | indent }}
        </pre>

    .. raw:: latex

        \\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]
{{ output.data[datatype] | escape_latex | ansi2latex | indent | indent }}
        \\end{sphinxVerbatim}

{%- elif datatype in ['image/svg+xml', 'image/png', 'image/jpeg', 'application/pdf'] %}

    .. image:: {{ output.metadata.filenames[datatype] | posix_path }}
{%- if datatype in output.metadata %}
{%- set width = output.metadata[datatype].width %}
{%- if width %}
        :width: {{ width }}
{%- endif %}
{%- set height = output.metadata[datatype].height %}
{%- if height %}
        :height: {{ height }}
{% endif %}
{% endif %}
{%- elif datatype in ['text/markdown'] %}

{{ output.data['text/markdown'] | markdown2rst | indent }}
{%- elif datatype in ['text/latex'] %}

    .. math::
        :nowrap:

{{ output.data['text/latex'] | indent | indent }}
{%- elif datatype == 'text/html' %}
    :class: rendered_html

    .. raw:: html

{{ output.data['text/html'] | indent | indent }}
{%- elif datatype == 'application/javascript' %}

    .. raw:: html

        <div class="output_javascript"></div>
        <script type="text/javascript">
        var element = document.currentScript.previousSibling.previousSibling;
{{ output.data['application/javascript'] | indent | indent }}
        </script>
{%- elif datatype.startswith('application/vnd.jupyter') and datatype.endswith('+json') %}

    .. raw:: html

        <script type="{{ datatype }}">{{ output.data[datatype] | json_dumps }}</script>
{% else %}

    .. nbwarning:: Data type cannot be displayed: {{ datatype }}
{%- endif %}
{% endmacro %}


{% block nboutput -%}
{%- set html_datatype, latex_datatype = output | get_output_type %}
{%- if html_datatype == latex_datatype %}
{{ insert_nboutput(html_datatype, output, cell) }}
{% else %}
.. only:: html

{{ insert_nboutput(html_datatype, output, cell) | indent }}
.. only:: latex

{{ insert_nboutput(latex_datatype, output, cell) | indent }}
{% endif %}
{% endblock nboutput %}


{% block execute_result %}{{ self.nboutput() }}{% endblock execute_result %}
{% block display_data %}{{ self.nboutput() }}{% endblock display_data %}
{% block stream %}{{ self.nboutput() }}{% endblock stream %}
{% block error %}{{ self.nboutput() }}{% endblock error %}


{% block markdowncell %}
{%- if 'nbsphinx-toctree' in cell.metadata %}
{{ cell | extract_toctree }}
{%- else %}
{{ cell | save_attachments or super() | replace_attachments }}
{% endif %}
{% endblock markdowncell %}


{% block rawcell %}
{%- set raw_mimetype = cell.metadata.get('raw_mimetype', '').lower() %}
{%- if raw_mimetype == '' %}
.. raw:: html

{{ cell.source | indent }}

.. raw:: latex

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/html' %}
.. raw:: html

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/latex' %}
.. raw:: latex

{{ cell.source | indent }}
{%- elif raw_mimetype == 'text/markdown' %}
..
{# Empty comment to make sure the preceding directive (if any) is closed #}
{{ cell.source | markdown2rst }}
{%- elif raw_mimetype == 'text/restructuredtext' %}
..
{# Empty comment to make sure the preceding directive (if any) is closed #}
{{ cell.source }}
{% endif %}
{% endblock rawcell %}


{% block footer %}

{% if 'application/vnd.jupyter.widget-state+json' in nb.metadata.widgets %}

.. raw:: html

    <script type="application/vnd.jupyter.widget-state+json">
    {{ nb.metadata.widgets['application/vnd.jupyter.widget-state+json'] | json_dumps }}
    </script>
{% endif %}
{{ super() }}
{% endblock footer %}
""".replace('__RST_DEFAULT_TEMPLATE__', nbconvert.RSTExporter().template_file)


LATEX_PREAMBLE = r"""
% Jupyter Notebook code cell colors
\definecolor{nbsphinxin}{HTML}{307FC1}
\definecolor{nbsphinxout}{HTML}{BF5B3D}
\definecolor{nbsphinx-code-bg}{HTML}{F5F5F5}
\definecolor{nbsphinx-code-border}{HTML}{E0E0E0}
\definecolor{nbsphinx-stderr}{HTML}{FFDDDD}
% ANSI colors for output streams and traceback highlighting
\definecolor{ansi-black}{HTML}{3E424D}
\definecolor{ansi-black-intense}{HTML}{282C36}
\definecolor{ansi-red}{HTML}{E75C58}
\definecolor{ansi-red-intense}{HTML}{B22B31}
\definecolor{ansi-green}{HTML}{00A250}
\definecolor{ansi-green-intense}{HTML}{007427}
\definecolor{ansi-yellow}{HTML}{DDB62B}
\definecolor{ansi-yellow-intense}{HTML}{B27D12}
\definecolor{ansi-blue}{HTML}{208FFB}
\definecolor{ansi-blue-intense}{HTML}{0065CA}
\definecolor{ansi-magenta}{HTML}{D160C4}
\definecolor{ansi-magenta-intense}{HTML}{A03196}
\definecolor{ansi-cyan}{HTML}{60C6C8}
\definecolor{ansi-cyan-intense}{HTML}{258F8F}
\definecolor{ansi-white}{HTML}{C5C1B4}
\definecolor{ansi-white-intense}{HTML}{A1A6B2}
\definecolor{ansi-default-inverse-fg}{HTML}{FFFFFF}
\definecolor{ansi-default-inverse-bg}{HTML}{000000}

% Define an environment for non-plain-text code cell outputs (e.g. images)
\makeatletter
\newenvironment{nbsphinxfancyoutput}{%
    % Avoid fatal error with framed.sty if graphics too long to fit on one page
    \let\sphinxincludegraphics\nbsphinxincludegraphics
    \nbsphinx@image@maxheight\textheight
    \advance\nbsphinx@image@maxheight -2\fboxsep   % default \fboxsep 3pt
    \advance\nbsphinx@image@maxheight -2\fboxrule  % default \fboxrule 0.4pt
    \advance\nbsphinx@image@maxheight -\baselineskip
\def\nbsphinxfcolorbox{\spx@fcolorbox{nbsphinx-code-border}{white}}%
\def\FrameCommand{\nbsphinxfcolorbox\nbsphinxfancyaddprompt\@empty}%
\def\FirstFrameCommand{\nbsphinxfcolorbox\nbsphinxfancyaddprompt\sphinxVerbatim@Continues}%
\def\MidFrameCommand{\nbsphinxfcolorbox\sphinxVerbatim@Continued\sphinxVerbatim@Continues}%
\def\LastFrameCommand{\nbsphinxfcolorbox\sphinxVerbatim@Continued\@empty}%
\MakeFramed{\advance\hsize-\width\@totalleftmargin\z@\linewidth\hsize\@setminipage}%
\lineskip=1ex\lineskiplimit=1ex\raggedright%
}{\par\unskip\@minipagefalse\endMakeFramed}
\makeatother
\newbox\nbsphinxpromptbox
\def\nbsphinxfancyaddprompt{\ifvoid\nbsphinxpromptbox\else
    \kern\fboxrule\kern\fboxsep
    \copy\nbsphinxpromptbox
    \kern-\ht\nbsphinxpromptbox\kern-\dp\nbsphinxpromptbox
    \kern-\fboxsep\kern-\fboxrule\nointerlineskip
    \fi}
\newlength\nbsphinxcodecellspacing
\setlength{\nbsphinxcodecellspacing}{0pt}

% Define support macros for attaching opening and closing lines to notebooks
\newsavebox\nbsphinxbox
\makeatletter
\newcommand{\nbsphinxstartnotebook}[1]{%
    \par
    % measure needed space
    \setbox\nbsphinxbox\vtop{{#1\par}}
    % reserve some space at bottom of page, else start new page
    \needspace{\dimexpr2.5\baselineskip+\ht\nbsphinxbox+\dp\nbsphinxbox}
    % mimick vertical spacing from \section command
      \addpenalty\@secpenalty
      \@tempskipa 3.5ex \@plus 1ex \@minus .2ex\relax
      \addvspace\@tempskipa
      {\Large\@tempskipa\baselineskip
             \advance\@tempskipa-\prevdepth
             \advance\@tempskipa-\ht\nbsphinxbox
             \ifdim\@tempskipa>\z@
               \vskip \@tempskipa
             \fi}
    \unvbox\nbsphinxbox
    % if notebook starts with a \section, prevent it from adding extra space
    \@nobreaktrue\everypar{\@nobreakfalse\everypar{}}%
    % compensate the parskip which will get inserted by next paragraph
    \nobreak\vskip-\parskip
    % do not break here
    \nobreak
}% end of \nbsphinxstartnotebook

\newcommand{\nbsphinxstopnotebook}[1]{%
    \par
    % measure needed space
    \setbox\nbsphinxbox\vbox{{#1\par}}
    \nobreak % it updates page totals
    \dimen@\pagegoal
    \advance\dimen@-\pagetotal \advance\dimen@-\pagedepth
    \advance\dimen@-\ht\nbsphinxbox \advance\dimen@-\dp\nbsphinxbox
    \ifdim\dimen@<\z@
      % little space left
      \unvbox\nbsphinxbox
      \kern-.8\baselineskip
      \nobreak\vskip\z@\@plus1fil
      \penalty100
      \vskip\z@\@plus-1fil
      \kern.8\baselineskip
    \else
      \unvbox\nbsphinxbox
    \fi
}% end of \nbsphinxstopnotebook

% Ensure height of an included graphics fits in nbsphinxfancyoutput frame
\newdimen\nbsphinx@image@maxheight % set in nbsphinxfancyoutput environment
\newcommand*{\nbsphinxincludegraphics}[2][]{%
    \gdef\spx@includegraphics@options{#1}%
    \setbox\spx@image@box\hbox{\includegraphics[#1,draft]{#2}}%
    \in@false
    \ifdim \wd\spx@image@box>\linewidth
      \g@addto@macro\spx@includegraphics@options{,width=\linewidth}%
      \in@true
    \fi
    % no rotation, no need to worry about depth
    \ifdim \ht\spx@image@box>\nbsphinx@image@maxheight
      \g@addto@macro\spx@includegraphics@options{,height=\nbsphinx@image@maxheight}%
      \in@true
    \fi
    \ifin@
      \g@addto@macro\spx@includegraphics@options{,keepaspectratio}%
    \fi
    \setbox\spx@image@box\box\voidb@x % clear memory
    \expandafter\includegraphics\expandafter[\spx@includegraphics@options]{#2}%
}% end of "\MakeFrame"-safe variant of \sphinxincludegraphics
\makeatother

\makeatletter
\renewcommand*\sphinx@verbatim@nolig@list{\do\'\do\`}
\begingroup
\catcode`'=\active
\let\nbsphinx@noligs\@noligs
\g@addto@macro\nbsphinx@noligs{\let'\PYGZsq}
\endgroup
\makeatother
\renewcommand*\sphinxbreaksbeforeactivelist{\do\<\do\"\do\'}
\renewcommand*\sphinxbreaksafteractivelist{\do\.\do\,\do\:\do\;\do\?\do\!\do\/\do\>\do\-}
\makeatletter
\fvset{codes*=\sphinxbreaksattexescapedchars\do\^\^\let\@noligs\nbsphinx@noligs}
\makeatother
"""


CSS_STRING = """
/* CSS for nbsphinx extension */

/* remove conflicting styling from Sphinx themes */
div.nbinput.container,
div.nbinput.container div.prompt,
div.nbinput.container div.input_area,
div.nbinput.container div[class*=highlight],
div.nbinput.container div[class*=highlight] pre,
div.nboutput.container,
div.nboutput.container div.prompt,
div.nboutput.container div.output_area,
div.nboutput.container div[class*=highlight],
div.nboutput.container div[class*=highlight] pre {
    background: none;
    border: none;
    padding: 0 0;
    margin: 0;
    box-shadow: none;
}

/* avoid gaps between output lines */
div.nboutput.container div[class*=highlight] pre {
    line-height: normal;
}

/* input/output containers */
div.nbinput.container,
div.nboutput.container {
    display: -webkit-flex;
    display: flex;
    align-items: flex-start;
    margin: 0;
    width: 100%%;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput.container,
    div.nboutput.container {
        flex-direction: column;
    }
}

/* input container */
div.nbinput.container {
    padding-top: 5px;
}

/* last container */
div.nblast.container {
    padding-bottom: 5px;
}

/* input prompt */
div.nbinput.container div.prompt pre {
    color: #307FC1;
}

/* output prompt */
div.nboutput.container div.prompt pre {
    color: #BF5B3D;
}

/* all prompts */
div.nbinput.container div.prompt,
div.nboutput.container div.prompt {
    min-width: %(nbsphinx_prompt_width)s;
    padding-top: 0.3rem;
    padding-right: 0.3rem;
    text-align: right;
    flex: 0;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput.container div.prompt,
    div.nboutput.container div.prompt {
        text-align: left;
        padding: 0.4em;
    }
    div.nboutput.container div.prompt.empty {
        padding: 0;
    }
}

/* disable scrollbars on prompts */
div.nbinput.container div.prompt pre,
div.nboutput.container div.prompt pre {
    overflow: hidden;
}

/* input/output area */
div.nbinput.container div.input_area,
div.nboutput.container div.output_area {
    -webkit-flex: 1;
    flex: 1;
    overflow: auto;
}
@media (max-width: %(nbsphinx_responsive_width)s) {
    div.nbinput.container div.input_area,
    div.nboutput.container div.output_area {
        width: 100%%;
    }
}

/* input area */
div.nbinput.container div.input_area {
    border: 1px solid #e0e0e0;
    border-radius: 2px;
    background: #f5f5f5;
}

/* override MathJax center alignment in output cells */
div.nboutput.container div[class*=MathJax] {
    text-align: left !important;
}

/* override sphinx.ext.imgmath center alignment in output cells */
div.nboutput.container div.math p {
    text-align: left;
}

/* standard error */
div.nboutput.container div.output_area.stderr {
    background: #fdd;
}

/* ANSI colors */
.ansi-black-fg { color: #3E424D; }
.ansi-black-bg { background-color: #3E424D; }
.ansi-black-intense-fg { color: #282C36; }
.ansi-black-intense-bg { background-color: #282C36; }
.ansi-red-fg { color: #E75C58; }
.ansi-red-bg { background-color: #E75C58; }
.ansi-red-intense-fg { color: #B22B31; }
.ansi-red-intense-bg { background-color: #B22B31; }
.ansi-green-fg { color: #00A250; }
.ansi-green-bg { background-color: #00A250; }
.ansi-green-intense-fg { color: #007427; }
.ansi-green-intense-bg { background-color: #007427; }
.ansi-yellow-fg { color: #DDB62B; }
.ansi-yellow-bg { background-color: #DDB62B; }
.ansi-yellow-intense-fg { color: #B27D12; }
.ansi-yellow-intense-bg { background-color: #B27D12; }
.ansi-blue-fg { color: #208FFB; }
.ansi-blue-bg { background-color: #208FFB; }
.ansi-blue-intense-fg { color: #0065CA; }
.ansi-blue-intense-bg { background-color: #0065CA; }
.ansi-magenta-fg { color: #D160C4; }
.ansi-magenta-bg { background-color: #D160C4; }
.ansi-magenta-intense-fg { color: #A03196; }
.ansi-magenta-intense-bg { background-color: #A03196; }
.ansi-cyan-fg { color: #60C6C8; }
.ansi-cyan-bg { background-color: #60C6C8; }
.ansi-cyan-intense-fg { color: #258F8F; }
.ansi-cyan-intense-bg { background-color: #258F8F; }
.ansi-white-fg { color: #C5C1B4; }
.ansi-white-bg { background-color: #C5C1B4; }
.ansi-white-intense-fg { color: #A1A6B2; }
.ansi-white-intense-bg { background-color: #A1A6B2; }

.ansi-default-inverse-fg { color: #FFFFFF; }
.ansi-default-inverse-bg { background-color: #000000; }

.ansi-bold { font-weight: bold; }
.ansi-underline { text-decoration: underline; }


div.nbinput.container div.input_area div[class*=highlight] > pre,
div.nboutput.container div.output_area div[class*=highlight] > pre,
div.nboutput.container div.output_area div[class*=highlight].math,
div.nboutput.container div.output_area.rendered_html,
div.nboutput.container div.output_area > div.output_javascript,
div.nboutput.container div.output_area:not(.rendered_html) > img{
    padding: 0.3rem;
}

/* fix copybtn overflow problem in chromium (needed for 'sphinx_copybutton') */
div.nbinput.container div.input_area > div[class^='highlight'],
div.nboutput.container div.output_area > div[class^='highlight']{
    overflow-y: hidden;
}

/* hide copybtn icon on prompts (needed for 'sphinx_copybutton') */
.prompt a.copybtn {
    display: none;
}

/* Some additional styling taken form the Jupyter notebook CSS */
div.rendered_html table {
  border: none;
  border-collapse: collapse;
  border-spacing: 0;
  color: black;
  font-size: 12px;
  table-layout: fixed;
}
div.rendered_html thead {
  border-bottom: 1px solid black;
  vertical-align: bottom;
}
div.rendered_html tr,
div.rendered_html th,
div.rendered_html td {
  text-align: right;
  vertical-align: middle;
  padding: 0.5em 0.5em;
  line-height: normal;
  white-space: normal;
  max-width: none;
  border: none;
}
div.rendered_html th {
  font-weight: bold;
}
div.rendered_html tbody tr:nth-child(odd) {
  background: #f5f5f5;
}
div.rendered_html tbody tr:hover {
  background: rgba(66, 165, 245, 0.2);
}
"""

CSS_STRING_READTHEDOCS = """
/* CSS overrides for sphinx_rtd_theme */

/* 24px margin */
.nbinput.nblast.container,
.nboutput.nblast.container {
    margin-bottom: 19px;  /* padding has already 5px */
}

/* ... except between code cells! */
.nblast.container + .nbinput.container {
    margin-top: -19px;
}

.admonition > p:before {
    margin-right: 4px;  /* make room for the exclamation icon */
}

/* Fix math alignment, see https://github.com/rtfd/sphinx_rtd_theme/pull/686 */
.math {
    text-align: unset;
}
"""

CSS_STRING_CLOUD = """
/* CSS overrides for cloud theme */

/* nicer titles and more space for info and warning logos */

div.admonition p.admonition-title {
    background: rgba(0, 0, 0, .05);
    margin: .5em -1em;
    margin-top: -.5em !important;
    padding: .5em .5em .5em 2.65em;
}

/* indent single paragraph */
div.admonition {
    text-indent: 20px;
}
/* don't indent multiple paragraphs */
div.admonition > p {
    text-indent: 0;
}
/* remove excessive padding */
div.admonition.inline-title p.admonition-title {
    padding-left: .2em;
}
"""


class Exporter(nbconvert.RSTExporter):
    """Convert Jupyter notebooks to reStructuredText.

    Uses nbconvert to convert Jupyter notebooks to a reStructuredText
    string with custom reST directives for input and output cells.

    Notebooks without output cells are automatically executed before
    conversion.

    """

    def __init__(self, execute='auto', kernel_name='', execute_arguments=[],
                 allow_errors=False, timeout=30, codecell_lexer='none'):
        """Initialize the Exporter."""

        # NB: The following stateful Jinja filters are a hack until
        # template-based processing is dropped
        # (https://github.com/spatialaudio/nbsphinx/issues/36) or someone
        # comes up with a better idea.

        # NB: This instance-local state makes the methods non-reentrant!
        attachment_storage = []

        def save_attachments(cell):
            for filename, bundle in cell.get('attachments', {}).items():
                attachment_storage.append((filename, bundle))

        def replace_attachments(text):
            for filename, bundle in attachment_storage:
                # For now, this works only if there is a single MIME bundle
                (mime_type, data), = bundle.items()
                text = re.sub(
                    r'^(\s*\.\. (\|[^|]*\| image|figure)::) attachment:{0}$'
                        .format(filename),
                    r'\1 data:{0};base64,{1}'.format(mime_type, data),
                    text, flags=re.MULTILINE)
            del attachment_storage[:]
            return text

        self._execute = execute
        self._kernel_name = kernel_name
        self._execute_arguments = execute_arguments
        self._allow_errors = allow_errors
        self._timeout = timeout
        self._codecell_lexer = codecell_lexer
        loader = jinja2.DictLoader({'nbsphinx-rst.tpl': RST_TEMPLATE})
        super(Exporter, self).__init__(
            template_file='nbsphinx-rst.tpl', extra_loaders=[loader],
            config=traitlets.config.Config({
                'HighlightMagicsPreprocessor': {'enabled': True},
                # Work around https://github.com/jupyter/nbconvert/issues/720:
                'RegexRemovePreprocessor': {'enabled': False},
            }),
            filters={
                'convert_pandoc': convert_pandoc,
                'markdown2rst': markdown2rst,
                'get_empty_lines': _get_empty_lines,
                'extract_toctree': _extract_toctree,
                'save_attachments': save_attachments,
                'replace_attachments': replace_attachments,
                'get_output_type': _get_output_type,
                'json_dumps': json.dumps,
                'basename': os.path.basename,
                'dirname': os.path.dirname,
            })

    def from_notebook_node(self, nb, resources=None, **kw):
        nb = copy.deepcopy(nb)
        if resources is None:
            resources = {}
        else:
            resources = copy.deepcopy(resources)
        # Set default codecell lexer
        resources['codecell_lexer'] = self._codecell_lexer

        nbsphinx_metadata = nb.metadata.get('nbsphinx', {})

        execute = nbsphinx_metadata.get('execute', self._execute)
        if execute not in ('always', 'never', 'auto'):
            raise ValueError('invalid execute option: {!r}'.format(execute))
        auto_execute = (
            execute == 'auto' and
            # At least one code cell actually containing source code:
            any(c.source for c in nb.cells if c.cell_type == 'code') and
            # No outputs, not even a prompt number:
            not any(c.get('outputs') or c.get('execution_count')
                    for c in nb.cells if c.cell_type == 'code')
        )
        if auto_execute or execute == 'always':
            allow_errors = nbsphinx_metadata.get(
                'allow_errors', self._allow_errors)
            timeout = nbsphinx_metadata.get('timeout', self._timeout)
            pp = nbconvert.preprocessors.ExecutePreprocessor(
                kernel_name=self._kernel_name,
                extra_arguments=self._execute_arguments,
                allow_errors=allow_errors, timeout=timeout)
            nb, resources = pp.preprocess(nb, resources)

        if 'nbsphinx_save_notebook' in resources:
            # Save *executed* notebook *before* the Exporter can change it:
            nbformat.write(nb, resources['nbsphinx_save_notebook'])

        # Call into RSTExporter
        rststr, resources = super(Exporter, self).from_notebook_node(
            nb, resources, **kw)

        orphan = nbsphinx_metadata.get('orphan', False)
        if orphan is True:
            resources['nbsphinx_orphan'] = True
        elif orphan is not False:
            raise ValueError('invalid orphan option: {!r}'.format(orphan))

        if 'application/vnd.jupyter.widget-state+json' in nb.metadata.get(
                'widgets', {}):
            resources['nbsphinx_widgets'] = True

        return rststr, resources


class NotebookParser(rst.Parser):
    """Sphinx source parser for Jupyter notebooks.

    Uses nbsphinx.Exporter to convert notebook content to a
    reStructuredText string, which is then parsed by Sphinx's built-in
    reST parser.

    """

    supported = 'jupyter_notebook',

    def get_transforms(self):
        """List of transforms for documents parsed by this parser."""
        return rst.Parser.get_transforms(self) + [
            CreateNotebookSectionAnchors,
            ReplaceAlertDivs,
            CopyLinkedFiles,
        ]

    def parse(self, inputstring, document):
        """Parse *inputstring*, write results to *document*.

        *inputstring* is either the JSON representation of a notebook,
        or a paragraph of text coming from the Sphinx translation
        machinery.

        Note: For now, the translation strings use reST formatting,
        because the NotebookParser uses reST as intermediate
        representation.
        However, there are plans to remove this intermediate step
        (https://github.com/spatialaudio/nbsphinx/issues/36), and after
        that, the translated strings will most likely be parsed as
        CommonMark.

        If the configuration value "nbsphinx_custom_formats" is
        specified, the input string is converted to the Jupyter notebook
        format with the given conversion function.

        """
        env = document.settings.env
        formats = {
            '.ipynb': lambda s: nbformat.reads(s, as_version=_ipynbversion)}
        formats.update(env.config.nbsphinx_custom_formats)
        suffix = os.path.splitext(env.doc2path(env.docname))[1]
        try:
            converter = formats[suffix]
        except KeyError:
            raise NotebookError('No converter for suffix {!r}'.format(suffix))
        if isinstance(converter, str):
            converter = sphinx.util.import_object(converter)
        try:
            nb = converter(inputstring)
        except Exception:
            # NB: The use of the RST parser is temporary!
            rst.Parser.parse(self, inputstring, document)
            return

        srcdir = os.path.dirname(env.doc2path(env.docname))
        auxdir = env.nbsphinx_auxdir

        resources = {}
        # Working directory for ExecutePreprocessor
        resources['metadata'] = {'path': srcdir}
        # Sphinx doesn't accept absolute paths in images etc.
        resources['output_files_dir'] = os.path.relpath(auxdir, srcdir)
        resources['unique_key'] = re.sub('[/ ]', '_', env.docname)

        # NB: The source file could have a different suffix
        #     if nbsphinx_custom_formats is used.
        notebookfile = env.docname + '.ipynb'
        env.nbsphinx_notebooks[env.docname] = notebookfile
        auxfile = os.path.join(auxdir, notebookfile)
        sphinx.util.ensuredir(os.path.dirname(auxfile))
        resources['nbsphinx_save_notebook'] = auxfile

        exporter = Exporter(
            execute=env.config.nbsphinx_execute,
            kernel_name=env.config.nbsphinx_kernel_name,
            execute_arguments=env.config.nbsphinx_execute_arguments,
            allow_errors=env.config.nbsphinx_allow_errors,
            timeout=env.config.nbsphinx_timeout,
            codecell_lexer=env.config.nbsphinx_codecell_lexer,
        )

        try:
            rststring, resources = exporter.from_notebook_node(nb, resources)
        except nbconvert.preprocessors.execute.CellExecutionError as e:
            lines = str(e).split('\n')
            lines[0] = 'CellExecutionError in {}:'.format(
                env.doc2path(env.docname, base=None))
            lines.append("You can ignore this error by setting the following "
                         "in conf.py:\n\n    nbsphinx_allow_errors = True\n")
            raise NotebookError('\n'.join(lines))
        except Exception as e:
            raise NotebookError(type(e).__name__ + ' in ' +
                                env.doc2path(env.docname, base=None) + ':\n' +
                                str(e))

        rststring = """
.. role:: nbsphinx-math(raw)
    :format: latex + html
    :class: math

..

""" + rststring

        # Create additional output files (figures etc.),
        # see nbconvert.writers.FilesWriter.write()
        for filename, data in resources.get('outputs', {}).items():
            dest = os.path.normpath(os.path.join(srcdir, filename))
            with open(dest, 'wb') as f:
                f.write(data)

        if resources.get('nbsphinx_orphan', False):
            rst.Parser.parse(self, ':orphan:', document)
        if env.config.nbsphinx_prolog:
            prolog = exporter.environment.from_string(
                env.config.nbsphinx_prolog).render(env=env)
            rst.Parser.parse(self, prolog, document)
        rst.Parser.parse(self, rststring, document)
        if env.config.nbsphinx_epilog:
            epilog = exporter.environment.from_string(
                env.config.nbsphinx_epilog).render(env=env)
            rst.Parser.parse(self, epilog, document)

        if resources.get('nbsphinx_widgets', False):
            env.nbsphinx_widgets.add(env.docname)


class NotebookError(sphinx.errors.SphinxError):
    """Error during notebook parsing."""

    category = 'Notebook error'


class CodeAreaNode(docutils.nodes.Element):
    """Input area or plain-text output area of a Jupyter notebook code cell."""


class FancyOutputNode(docutils.nodes.Element):
    """A custom node for non-plain-text output of code cells."""


def _create_code_nodes(directive):
    """Create nodes for an input or output code cell."""
    directive.state.document['nbsphinx_include_css'] = True
    execution_count = directive.options.get('execution-count')
    config = directive.state.document.settings.env.config
    if isinstance(directive, NbInput):
        outer_classes = ['nbinput']
        if 'no-output' in directive.options:
            outer_classes.append('nblast')
        inner_classes = ['input_area']
        prompt_template = config.nbsphinx_input_prompt
        if not execution_count:
            execution_count = ' '
    elif isinstance(directive, NbOutput):
        outer_classes = ['nboutput']
        if 'more-to-come' not in directive.options:
            outer_classes.append('nblast')
        inner_classes = ['output_area']
        inner_classes.append(directive.options.get('class', ''))
        prompt_template = config.nbsphinx_output_prompt
    else:
        assert False

    outer_node = docutils.nodes.container(classes=outer_classes)
    if execution_count:
        prompt = prompt_template % (execution_count,)
        prompt_node = docutils.nodes.literal_block(
            prompt, prompt, language='none', classes=['prompt'])
    else:
        prompt = ''
        prompt_node = docutils.nodes.container(classes=['prompt', 'empty'])
    # NB: Prompts are added manually in LaTeX output
    outer_node += sphinx.addnodes.only('', prompt_node, expr='html')

    if isinstance(directive, NbInput):
        text = '\n'.join(directive.content.data)
        if directive.arguments:
            language = directive.arguments[0]
        else:
            language = 'none'
        inner_node = docutils.nodes.literal_block(
            text, text, language=language, classes=inner_classes)
    else:
        inner_node = docutils.nodes.container(classes=inner_classes)
        sphinx.util.nodes.nested_parse_with_titles(
            directive.state, directive.content, inner_node)

    if 'fancy' in directive.options:
        outer_node += FancyOutputNode('', inner_node, prompt=prompt)
    else:
        codearea_node = CodeAreaNode(
            '', inner_node, prompt=prompt, stderr='stderr' in inner_classes)
        # See http://stackoverflow.com/q/34050044/.
        for attr in 'empty-lines-before', 'empty-lines-after':
            value = directive.options.get(attr, 0)
            if value:
                codearea_node[attr] = value
        outer_node += codearea_node
    return [outer_node]


class AdmonitionNode(docutils.nodes.Element):
    """A custom node for info and warning boxes."""


# See http://docutils.sourceforge.net/docs/howto/rst-directives.html

class NbInput(rst.Directive):
    """A notebook input cell with prompt and code area."""

    required_arguments = 0
    optional_arguments = 1  # lexer name
    final_argument_whitespace = False
    option_spec = {
        'execution-count': rst.directives.positive_int,
        'empty-lines-before': rst.directives.nonnegative_int,
        'empty-lines-after': rst.directives.nonnegative_int,
        'no-output': rst.directives.flag,
    }
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        return _create_code_nodes(self)


class NbOutput(rst.Directive):
    """A notebook output cell with optional prompt."""

    required_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'execution-count': rst.directives.positive_int,
        'more-to-come': rst.directives.flag,
        'fancy': rst.directives.flag,
        'class': rst.directives.unchanged,
    }
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        return _create_code_nodes(self)


class _NbAdmonition(rst.Directive):
    """Base class for NbInfo and NbWarning."""

    required_arguments = 0
    optional_arguments = 0
    option_spec = {}
    has_content = True

    def run(self):
        """This is called by the reST parser."""
        node = AdmonitionNode(classes=['admonition', self._class])
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class NbInfo(_NbAdmonition):
    """An information box."""

    _class = 'note'


class NbWarning(_NbAdmonition):
    """A warning box."""

    _class = 'warning'


def convert_pandoc(text, from_format, to_format):
    """Simple wrapper for markdown2rst.

    In nbconvert version 5.0, the use of markdown2rst in the RST
    template was replaced by the new filter function convert_pandoc.

    """
    if from_format != 'markdown' and to_format != 'rst':
        raise ValueError('Unsupported conversion')
    return markdown2rst(text)


class CitationParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if self._check_cite(attrs):
            self.starttag = tag

    def handle_endtag(self, tag):
        self.endtag = tag

    def handle_startendtag(self, tag, attrs):
        self._check_cite(attrs)

    def _check_cite(self, attrs):
        for name, value in attrs:
            if name == 'data-cite':
                self.cite = ':cite:`' + value + '`'
                return True
        return False

    def reset(self):
        HTMLParser.reset(self)
        self.starttag = ''
        self.endtag = ''
        self.cite = ''


def markdown2rst(text):
    """Convert a Markdown string to reST via pandoc.

    This is very similar to nbconvert.filters.markdown.markdown2rst(),
    except that it uses a pandoc filter to convert raw LaTeX blocks to
    "math" directives (instead of "raw:: latex" directives).

    NB: At some point, pandoc changed its behavior!  In former times,
    it converted LaTeX math environments to RawBlock ("latex"), at some
    later point this was changed to RawInline ("tex").
    Either way, we convert it to Math/DisplayMath.

    """

    def parse_html(obj):
        p = CitationParser()
        p.feed(obj['c'][1])
        p.close()
        return p

    def object_hook(obj):
        if object_hook.open_cite_tag:
            if obj.get('t') == 'RawInline' and obj['c'][0] == 'html':
                p = parse_html(obj)
                if p.endtag == object_hook.open_cite_tag:
                    object_hook.open_cite_tag = ''
            return {'t': 'Str', 'c': ''}  # Object is replaced by empty string

        if obj.get('t') == 'RawBlock' and obj['c'][0] == 'latex':
            obj['t'] = 'Para'
            obj['c'] = [{
                't': 'Math',
                'c': [
                    {'t': 'DisplayMath', 'c': []},
                    # Special marker characters are removed below:
                    '\x0e:nowrap:\x0f\n\n' + obj['c'][1],
                ]
            }]
        elif obj.get('t') == 'RawInline' and obj['c'][0] == 'tex':
            obj = {'t': 'RawInline',
                   'c': ['rst', ':nbsphinx-math:`{}`'.format(obj['c'][1])]}
        elif obj.get('t') == 'RawInline' and obj['c'][0] == 'html':
            p = parse_html(obj)
            if p.starttag:
                object_hook.open_cite_tag = p.starttag
            if p.cite:
                obj = {'t': 'RawInline', 'c': ['rst', p.cite]}
        return obj

    object_hook.open_cite_tag = ''

    def filter_func(text):
        json_data = json.loads(text, object_hook=object_hook)
        return json.dumps(json_data)

    input_format = 'markdown'
    input_format += '-implicit_figures'
    v = nbconvert.utils.pandoc.get_pandoc_version()
    if nbconvert.utils.version.check_version(v, '1.13'):
        input_format += '-native_divs+raw_html'

    rststring = pandoc(text, input_format, 'rst', filter_func=filter_func)
    return re.sub(r'^\n( *)\x0e:nowrap:\x0f$',
                  r'\1:nowrap:',
                  rststring,
                  flags=re.MULTILINE)


def pandoc(source, fmt, to, filter_func=None):
    """Convert a string in format `from` to format `to` via pandoc.

    This is based on nbconvert.utils.pandoc.pandoc() and extended to
    allow passing a filter function.

    """
    def encode(text):
        return text if isinstance(text, bytes) else text.encode('utf-8')

    def decode(data):
        return data.decode('utf-8') if isinstance(data, bytes) else data

    nbconvert.utils.pandoc.check_pandoc_version()
    v = nbconvert.utils.pandoc.get_pandoc_version()
    cmd = ['pandoc']
    if nbconvert.utils.version.check_version(v, '2.0'):
        # see issue #155
        cmd += ['--eol', 'lf']
    cmd1 = cmd + ['--from', fmt, '--to', 'json']
    cmd2 = cmd + ['--from', 'json', '--to', to]
    cmd2 += ['--columns=500']  # Avoid breaks in tables, see issue #240

    p = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    json_data, _ = p.communicate(encode(source))

    if filter_func:
        json_data = encode(filter_func(decode(json_data)))

    p = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = p.communicate(json_data)
    return decode(out).rstrip('\n')


def _extract_toctree(cell):
    """Extract links from Markdown cell and create toctree."""
    lines = ['.. toctree::']
    options = cell.metadata['nbsphinx-toctree']
    try:
        for option, value in options.items():
            if value is True:
                lines.append(':{}:'.format(option))
            elif value is False:
                pass
            else:
                lines.append(':{}: {}'.format(option, value))
    except AttributeError:
        raise ValueError(
            'invalid nbsphinx-toctree option: {!r}'.format(options))

    text = nbconvert.filters.markdown2rst(cell.source)
    settings = docutils.frontend.OptionParser(
        components=(rst.Parser,)).get_default_values()
    toctree_node = docutils.utils.new_document('extract_toctree', settings)
    parser = rst.Parser()
    parser.parse(text, toctree_node)

    if 'caption' not in options:
        for sec in toctree_node.traverse(docutils.nodes.section):
            assert sec.children
            assert isinstance(sec.children[0], docutils.nodes.title)
            title = sec.children[0].astext()
            lines.append(':caption: ' + title)
            break
    lines.append('')  # empty line
    for ref in toctree_node.traverse(docutils.nodes.reference):
        lines.append(ref.astext().replace('\n', '') +
                     ' <' + unquote(ref.get('refuri')) + '>')
    return '\n    '.join(lines)


def _get_empty_lines(text):
    """Get number of empty lines before and after code."""
    before = len(text) - len(text.lstrip('\n'))
    after = len(text) - len(text.strip('\n')) - before
    return before, after


def _get_output_type(output):
    """Choose appropriate output data types for HTML and LaTeX."""
    if output.output_type == 'stream':
        html_datatype = latex_datatype = 'text/plain'
        text = output.text
        output.data = {'text/plain': text[:-1] if text.endswith('\n') else text}
    elif output.output_type == 'error':
        html_datatype = latex_datatype = 'text/plain'
        output.data = {'text/plain': '\n'.join(output.traceback)}
    else:
        for datatype in DISPLAY_DATA_PRIORITY_HTML:
            if datatype in output.data:
                html_datatype = datatype
                break
        else:
            html_datatype = ', '.join(output.data.keys())
        for datatype in DISPLAY_DATA_PRIORITY_LATEX:
            if datatype in output.data:
                latex_datatype = datatype
                break
        else:
            latex_datatype = ', '.join(output.data.keys())
    return html_datatype, latex_datatype


def _local_file_from_reference(node, document):
    """Get local file path from reference and split it into components."""
    # NB: Anonymous hyperlinks must be already resolved at this point!
    refuri = node.get('refuri')
    if not refuri:
        refname = node.get('refname')
        if refname:
            refid = document.nameids.get(refname)
        else:
            # NB: This can happen for anonymous hyperlinks
            refid = node.get('refid')
        target = document.ids.get(refid)
        if not target:
            # No corresponding target, Sphinx may warn later
            return '', '', ''
        refuri = target.get('refuri')
        if not refuri:
            # Target doesn't have URI
            return '', '', ''
    if '://' in refuri:
        # Not a local link
        return '', '', ''
    elif refuri.startswith('#') or refuri.startswith('mailto:'):
        # Not a local link
        return '', '', ''

    # NB: We look for "fragment identifier" before unquoting
    match = re.match(r'^([^#]+)(\.[^#]+)(#.+)$', refuri)
    if match:
        base = unquote(match.group(1))
        # NB: The suffix and "fragment identifier" are not unquoted
        suffix = match.group(2)
        fragment = match.group(3)
    else:
        base, suffix = os.path.splitext(refuri)
        base = unquote(base)
        fragment = ''
    return base, suffix, fragment


class RewriteLocalLinks(docutils.transforms.Transform):
    """Turn links to source files into ``:doc:``/``:ref:`` links.

    Links to subsections are possible with ``...#Subsection-Title``.
    These links use the labels created by CreateSectionLabels.

    Links to subsections use ``:ref:``, links to whole source files use
    ``:doc:``.  Latter can be useful if you have an ``index.rst`` but
    also want a distinct ``index.ipynb`` for use with Jupyter.
    In this case you can use such a link in a notebook::

        [Back to main page](index.ipynb)

    In Jupyter, this will create a "normal" link to ``index.ipynb``, but
    in the files generated by Sphinx, this will become a link to the
    main page created from ``index.rst``.

    """

    default_priority = 500  # After AnonymousHyperlinks (440)

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            base, suffix, fragment = _local_file_from_reference(node,
                                                                self.document)
            if not base:
                continue

            for s in env.config.source_suffix:
                if suffix.lower() == s.lower():
                    target = base
                    if fragment:
                        target_ext = suffix + fragment
                        reftype = 'ref'
                    else:
                        target_ext = ''
                        reftype = 'doc'
                    break
            else:
                continue  # Not a link to a potential Sphinx source file

            target_docname = nbconvert.filters.posix_path(os.path.normpath(
                os.path.join(os.path.dirname(env.docname), target)))
            if target_docname in env.found_docs:
                reftarget = '/' + target_docname + target_ext
                if reftype == 'ref':
                    reftarget = reftarget.lower()
                linktext = node.astext()
                xref = sphinx.addnodes.pending_xref(
                    reftype=reftype, reftarget=reftarget, refdomain='std',
                    refwarn=True, refexplicit=True, refdoc=env.docname)
                xref += docutils.nodes.Text(linktext, linktext)
                node.replace_self(xref)


class CreateNotebookSectionAnchors(docutils.transforms.Transform):
    """Create section anchors for Jupyter notebooks.

    Note: Sphinx lower-cases the HTML section IDs, Jupyter doesn't.
    This transform creates anchors in the Jupyter style.

    """

    default_priority = 200  # Before CreateSectionLabels (250)

    def apply(self):
        all_ids = set()
        for section in self.document.traverse(docutils.nodes.section):
            title = section.children[0].astext()
            link_id = title.replace(' ', '-')
            if link_id in all_ids:
                # Avoid duplicated anchors on the same page
                continue
            all_ids.add(link_id)
            section['ids'] = [link_id]


class CreateSectionLabels(docutils.transforms.Transform):
    """Make labels for each document and each section thereof.

    These labels are referenced in RewriteLocalLinks but can also be
    used manually with ``:ref:``.

    """

    default_priority = 250  # Before references.PropagateTargets (260)

    def apply(self):
        env = self.document.settings.env
        file_ext = os.path.splitext(env.doc2path(env.docname))[1]
        i_still_have_to_create_the_document_label = True
        for section in self.document.traverse(docutils.nodes.section):
            assert section.children
            assert isinstance(section.children[0], docutils.nodes.title)
            title = section.children[0].astext()
            link_id = section['ids'][0]
            label = '/' + env.docname + file_ext + '#' + link_id
            label = label.lower()
            env.domaindata['std']['labels'][label] = (
                env.docname, link_id, title)
            env.domaindata['std']['anonlabels'][label] = (
                env.docname, link_id)

            # Create a label for the whole document using the first section:
            if i_still_have_to_create_the_document_label:
                label = '/' + env.docname.lower() + file_ext
                env.domaindata['std']['labels'][label] = (
                    env.docname, '', title)
                env.domaindata['std']['anonlabels'][label] = (
                    env.docname, '')
                i_still_have_to_create_the_document_label = False


class CreateDomainObjectLabels(docutils.transforms.Transform):
    """Create labels for domain-specific object signatures."""

    default_priority = 250  # About the same as CreateSectionLabels

    def apply(self):
        env = self.document.settings.env
        file_ext = os.path.splitext(env.doc2path(env.docname))[1]
        for sig in self.document.traverse(sphinx.addnodes.desc_signature):
            try:
                title = sig['ids'][0]
            except IndexError:
                # Object has same name as another, so skip it
                continue
            link_id = title.replace(' ', '-')
            sig['ids'] = [link_id]
            label = '/' + env.docname + file_ext + '#' + link_id
            label = label.lower()
            env.domaindata['std']['labels'][label] = (
                env.docname, link_id, title)
            env.domaindata['std']['anonlabels'][label] = (
                env.docname, link_id)


class ReplaceAlertDivs(docutils.transforms.Transform):
    """Replace certain <div> elements with AdmonitionNode containers.

    This is a quick-and-dirty work-around until a proper
    Mardown/CommonMark extension for note/warning boxes is available.

    """

    default_priority = 500  # Doesn't really matter

    _start_re = re.compile(
        r'\s*<div\s*class\s*=\s*(?P<q>"|\')([a-z\s-]*)(?P=q)\s*>\s*\Z',
        flags=re.IGNORECASE)
    _class_re = re.compile(r'\s*alert\s*alert-(info|warning)\s*\Z')
    _end_re = re.compile(r'\s*</div\s*>\s*\Z', flags=re.IGNORECASE)

    def apply(self):
        start_tags = []
        for node in self.document.traverse(docutils.nodes.raw):
            if node['format'] != 'html':
                continue
            start_match = self._start_re.match(node.astext())
            if not start_match:
                continue
            class_match = self._class_re.match(start_match.group(2))
            if not class_match:
                continue
            admonition_class = class_match.group(1)
            if admonition_class == 'info':
                admonition_class = 'note'
            start_tags.append((node, admonition_class))

        # Reversed order to allow nested <div> elements:
        for node, admonition_class in reversed(start_tags):
            content = []
            for sibling in node.traverse(include_self=False, descend=False,
                                         siblings=True, ascend=False):
                end_tag = (isinstance(sibling, docutils.nodes.raw) and
                           sibling['format'] == 'html' and
                           self._end_re.match(sibling.astext()))
                if end_tag:
                    admonition_node = AdmonitionNode(
                        classes=['admonition', admonition_class])
                    admonition_node.extend(content)
                    parent = node.parent
                    parent.replace(node, admonition_node)
                    for n in content:
                        parent.remove(n)
                    parent.remove(sibling)
                    break
                else:
                    content.append(sibling)


class CopyLinkedFiles(docutils.transforms.Transform):
    """Mark linked (local) files to be copied to the HTML output."""

    default_priority = 600  # After RewriteLocalLinks

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(docutils.nodes.reference):
            base, suffix, fragment = _local_file_from_reference(node,
                                                                self.document)
            if not base:
                continue  # Not a local link
            relpath = base + suffix + fragment
            file = os.path.normpath(
                os.path.join(os.path.dirname(env.docname), relpath))
            if not os.path.isfile(os.path.join(env.srcdir, file)):
                logger = sphinx.util.logging.getLogger(__name__)
                logger.warning('File not found: %r', file, location=node)
                continue  # Link is ignored
            elif file.startswith('..'):
                logger = sphinx.util.logging.getLogger(__name__)
                logger.warning('Link outside source directory: %r', file,
                               location=node)
                continue  # Link is ignored
            env.nbsphinx_files.setdefault(env.docname, []).append(file)


class GetSizeFromImages(
        sphinx.transforms.post_transforms.images.BaseImageConverter):
    """Get size from images and store it as node attributes.

    This is only done for LaTeX output.

    """

    # After ImageDownloader (100) and DataURIExtractor (150):
    default_priority = 200

    def match(self, node):
        return self.app.builder.format == 'latex'

    def handle(self, node):
        if 'width' not in node and 'height' not in node:
            srcdir = os.path.dirname(self.env.doc2path(self.env.docname))
            image_path = os.path.normpath(os.path.join(srcdir, node['uri']))
            size = sphinx.util.images.get_image_size(image_path)
            if size is not None:
                node['width'], node['height'] = map(str, size)


def config_inited(app, config):
    # Set default value for CSS prompt width (optimized for two-digit numbers)
    if config.nbsphinx_prompt_width is None:
        config.nbsphinx_prompt_width = {
            'agogo': '4.5ex',
            'alabaster': '5.5ex',
            'alabaster_jupyterhub': '5.5ex',
            'basicstrap': '5.5ex',
            'better': '4.5ex',
            'bizstyle': '5.5ex',
            'bootstrap': '5.5ex',
            'bootstrap-astropy': '5.5ex',
            'classic': '4.5ex',
            'cloud': '5ex',
            'dotted': '5ex',
            'greencloud': '5ex',
            'guzzle_sphinx_theme': '5.5ex',
            'haiku': '4.5ex',
            'julia': '5.5ex',
            'jupyter': '5.5ex',
            'maisie_sphinx_theme': '5.5ex',
            'nature': '5ex',
            'pandas_sphinx_theme': '5.5ex',
            'pangeo': '5ex',
            'pyramid': '4.5ex',
            'pytorch_sphinx_theme': '14ex',
            'redcloud': '5ex',
            'scrolls': '5.5ex',
            'sizzle': '5ex',
            'sphinxdoc': '5.5ex',
            'sphinx_material': '5.5ex',
            'sphinx_py3doc_enhanced_theme': '6.5ex',
            'sphinx_pyviz_theme': '5.5ex',
            'sphinx_rtd_theme': '5ex',
            'sphinx_typlog_theme': '5.5ex',
            'traditional': '5ex',
        }.get(config.html_theme, '7ex')

    for suffix in config.nbsphinx_custom_formats:
        app.add_source_suffix(suffix, 'jupyter_notebook')

    if config.nbsphinx_requirejs_path is None:
        config.nbsphinx_requirejs_path = 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js'
    if config.nbsphinx_requirejs_options is None:
        config.nbsphinx_requirejs_options = {
            'integrity': 'sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA=',
            'crossorigin': 'anonymous',
        }
    if config.nbsphinx_requirejs_path:
        # TODO: Add only on pages created from notebooks?
        app.add_js_file(
            config.nbsphinx_requirejs_path,
            **config.nbsphinx_requirejs_options)


def builder_inited(app):
    app.env.nbsphinx_notebooks = {}
    app.env.nbsphinx_files = {}
    app.env.nbsphinx_widgets = set()
    app.env.nbsphinx_auxdir = os.path.join(app.env.doctreedir, 'nbsphinx')
    sphinx.util.ensuredir(app.env.nbsphinx_auxdir)


def html_page_context(app, pagename, templatename, context, doctree):
    """Add CSS string to HTML pages that contain code cells."""
    style = ''
    if doctree and doctree.get('nbsphinx_include_css'):
        style += CSS_STRING % app.config
    if doctree and app.config.html_theme in ('sphinx_rtd_theme', 'julia'):
        style += CSS_STRING_READTHEDOCS
    if doctree and app.config.html_theme.endswith('cloud'):
        style += CSS_STRING_CLOUD
    if style:
        context['body'] = '\n<style>' + style + '</style>\n' + context['body']


def html_collect_pages(app):
    """This event handler is abused to copy local files around."""
    files = set()
    for file_list in app.env.nbsphinx_files.values():
        files.update(file_list)
    status_iterator = sphinx.util.status_iterator
    for file in status_iterator(files, 'copying linked files... ',
                                sphinx.util.console.brown, len(files)):
        target = os.path.join(app.builder.outdir, file)
        sphinx.util.ensuredir(os.path.dirname(target))
        try:
            sphinx.util.copyfile(os.path.join(app.env.srcdir, file), target)
        except OSError as err:
            logger = sphinx.util.logging.getLogger(__name__)
            logger.warning('Cannot copy local file %r: %s', file, err)
    notebooks = app.env.nbsphinx_notebooks.values()
    for notebook in status_iterator(
            notebooks, 'copying notebooks ... ',
            'brown', len(notebooks)):
        sphinx.util.copyfile(
            os.path.join(app.env.nbsphinx_auxdir, notebook),
            os.path.join(app.builder.outdir, notebook))
    return []  # No new HTML pages are created


def env_purge_doc(app, env, docname):
    """Remove list of local files for a given document."""
    try:
        del env.nbsphinx_notebooks[docname]
    except KeyError:
        pass
    try:
        del env.nbsphinx_files[docname]
    except KeyError:
        pass
    env.nbsphinx_widgets.discard(docname)


def env_updated(app, env):
    widgets_path = app.config.nbsphinx_widgets_path
    if widgets_path is None:
        if env.nbsphinx_widgets:
            try:
                from ipywidgets.embed import DEFAULT_EMBED_REQUIREJS_URL
            except ImportError:
                logger = sphinx.util.logging.getLogger(__name__)
                logger.warning(
                    'nbsphinx_widgets_path not given '
                    'and ipywidgets module unavailable')
            else:
                widgets_path = DEFAULT_EMBED_REQUIREJS_URL
        else:
            widgets_path = ''

    if widgets_path:
        app.add_js_file(widgets_path, **app.config.nbsphinx_widgets_options)


def depart_codearea_html(self, node):
    """Add empty lines before and after the code."""
    text = self.body[-1]
    text = text.replace('<pre>',
                        '<pre>\n' + '\n' * node.get('empty-lines-before', 0))
    text = text.replace('</pre>',
                        '\n' * node.get('empty-lines-after', 0) + '</pre>')
    self.body[-1] = text


def visit_codearea_latex(self, node):
    self.pushbody([])  # See popbody() below


def depart_codearea_latex(self, node):
    """Some changes to code blocks.

    * Change frame color and background color
    * Add empty lines before and after the code
    * Add prompt

    """
    lines = ''.join(self.popbody()).strip('\n').split('\n')
    out = []
    out.append('')
    out.append('{')  # Start a scope for colors
    if 'nbinput' in node.parent['classes']:
        promptcolor = 'nbsphinxin'
        out.append(r'\sphinxsetup{VerbatimColor={named}{nbsphinx-code-bg}}')
    else:
        out.append(r"""
\kern-\sphinxverbatimsmallskipamount\kern-\baselineskip
\kern+\FrameHeightAdjust\kern-\fboxrule
\vspace{\nbsphinxcodecellspacing}
""")
        promptcolor = 'nbsphinxout'
        if node['stderr']:
            out.append(r'\sphinxsetup{VerbatimColor={named}{nbsphinx-stderr}}')
        else:
            out.append(r'\sphinxsetup{VerbatimColor={named}{white}}')

    out.append(
        r'\sphinxsetup{VerbatimBorderColor={named}{nbsphinx-code-border}}')
    if lines[0].startswith(r'\fvset{'):  # Sphinx >= 1.6.6 and < 1.8.3
        out.append(lines[0])
        del lines[0]
    assert 'Verbatim' in lines[0]
    out.append(lines[0])
    code_lines = (
        [''] * node.get('empty-lines-before', 0) +
        lines[1:-1] +
        [''] * node.get('empty-lines-after', 0)
    )
    prompt = node['prompt']
    if prompt:
        prompt = nbconvert.filters.latex.escape_latex(prompt)
        prefix = r'\llap{\color{' + promptcolor + '}' + prompt + \
            r'\,\hspace{\fboxrule}\hspace{\fboxsep}}'
        assert code_lines
        code_lines[0] = prefix + code_lines[0]
    out.extend(code_lines)
    assert 'Verbatim' in lines[-1]
    out.append(lines[-1])
    out.append('}')  # End of scope for colors
    out.append('')
    self.body.append('\n'.join(out))


def visit_fancyoutput_latex(self, node):
    out = r"""
\hrule height -\fboxrule\relax
\vspace{\nbsphinxcodecellspacing}
"""
    prompt = node['prompt']
    if prompt:
        prompt = nbconvert.filters.latex.escape_latex(prompt)
        out += r"""
\savebox\nbsphinxpromptbox[0pt][r]{\color{nbsphinxout}\Verb|\strut{%s}\,|}
""" % (prompt,)
    else:
        out += r"""
\makeatletter\setbox\nbsphinxpromptbox\box\voidb@x\makeatother
"""
    out += r"""
\begin{nbsphinxfancyoutput}
"""
    self.body.append(out)


def depart_fancyoutput_latex(self, node):
    self.body.append('\n\\end{nbsphinxfancyoutput}\n')


def visit_admonition_html(self, node):
    self.body.append(self.starttag(node, 'div'))
    if len(node.children) >= 2:
        node[0]['classes'].append('admonition-title')
        html_theme = self.settings.env.config.html_theme
        if html_theme in ('sphinx_rtd_theme', 'julia'):
            node.children[0]['classes'].extend(['fa', 'fa-exclamation-circle'])


def depart_admonition_html(self, node):
    self.body.append('</div>\n')


def visit_admonition_latex(self, node):
    # See http://tex.stackexchange.com/q/305898/:
    self.body.append(
        '\n\\begin{sphinxadmonition}{' + node['classes'][1] + '}{}\\unskip')


def depart_admonition_latex(self, node):
    self.body.append('\\end{sphinxadmonition}\n')


def do_nothing(self, node):
    pass


def setup(app):
    """Initialize Sphinx extension."""
    app.add_source_suffix('.ipynb', 'jupyter_notebook')
    app.add_source_parser(NotebookParser)

    app.add_config_value('nbsphinx_execute', 'auto', rebuild='env')
    app.add_config_value('nbsphinx_kernel_name', '', rebuild='env')
    app.add_config_value('nbsphinx_execute_arguments', [], rebuild='env')
    app.add_config_value('nbsphinx_allow_errors', False, rebuild='')
    app.add_config_value('nbsphinx_timeout', 30, rebuild='')
    app.add_config_value('nbsphinx_codecell_lexer', 'none', rebuild='env')
    # Default value is set in config_inited():
    app.add_config_value('nbsphinx_prompt_width', None, rebuild='html')
    app.add_config_value('nbsphinx_responsive_width', '540px', rebuild='html')
    app.add_config_value('nbsphinx_prolog', None, rebuild='env')
    app.add_config_value('nbsphinx_epilog', None, rebuild='env')
    app.add_config_value('nbsphinx_input_prompt', '[%s]:', rebuild='env')
    app.add_config_value('nbsphinx_output_prompt', '[%s]:', rebuild='env')
    app.add_config_value('nbsphinx_custom_formats', {}, rebuild='env')
    # Default value is set in config_inited():
    app.add_config_value('nbsphinx_requirejs_path', None, rebuild='html')
    # Default value is set in config_inited():
    app.add_config_value('nbsphinx_requirejs_options', None, rebuild='html')
    # This will be updated in env_updated():
    app.add_config_value('nbsphinx_widgets_path', None, rebuild='html')
    app.add_config_value('nbsphinx_widgets_options', {}, rebuild='html')

    app.add_directive('nbinput', NbInput)
    app.add_directive('nboutput', NbOutput)
    app.add_directive('nbinfo', NbInfo)
    app.add_directive('nbwarning', NbWarning)
    app.add_node(CodeAreaNode,
                 html=(do_nothing, depart_codearea_html),
                 latex=(visit_codearea_latex, depart_codearea_latex))
    app.add_node(FancyOutputNode,
                 html=(do_nothing, do_nothing),
                 latex=(visit_fancyoutput_latex, depart_fancyoutput_latex))
    app.add_node(AdmonitionNode,
                 html=(visit_admonition_html, depart_admonition_html),
                 latex=(visit_admonition_latex, depart_admonition_latex))
    app.connect('builder-inited', builder_inited)
    app.connect('config-inited', config_inited)
    app.connect('html-page-context', html_page_context)
    app.connect('html-collect-pages', html_collect_pages)
    app.connect('env-purge-doc', env_purge_doc)
    app.connect('env-updated', env_updated)
    app.add_transform(CreateSectionLabels)
    app.add_transform(CreateDomainObjectLabels)
    app.add_transform(RewriteLocalLinks)
    app.add_post_transform(GetSizeFromImages)

    # Make docutils' "code" directive (generated by markdown2rst/pandoc)
    # behave like Sphinx's "code-block",
    # see https://github.com/sphinx-doc/sphinx/issues/2155:
    rst.directives.register_directive('code', sphinx.directives.code.CodeBlock)

    # Work-around until https://github.com/sphinx-doc/sphinx/pull/5504 is done:
    mathjax_config = app.config._raw_config.setdefault('mathjax_config', {})
    mathjax_config.setdefault(
        'tex2jax',
        {
            'inlineMath': [['$', '$'], ['\\(', '\\)']],
            'processEscapes': True,
            'ignoreClass': 'document',
            'processClass': 'math|output_area',
        }
    )

    # Add LaTeX definitions to preamble
    latex_elements = app.config._raw_config.setdefault('latex_elements', {})
    latex_elements['preamble'] = '\n'.join([
        LATEX_PREAMBLE,
        latex_elements.get('preamble', ''),
    ])

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'env_version': 2,
    }
