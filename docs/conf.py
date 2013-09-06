#!/usr/bin/env python3
# vim: set et sw=4 sts=4 fileencoding=utf-8:

# Copyright 2013 Dave Hughes.
#
# This file is part of picroscopy.
#
# picroscopy is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# picroscopy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# picroscopy.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import picroscopy

# -- General configuration -----------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = picroscopy.__name__.title()
copyright = '2013, %s' % picroscopy.__author__
version = picroscopy.__version__
release = picroscopy.__version__
exclude_patterns = ['_build']
pygments_style = 'sphinx'
#add_module_names = True
#modindex_common_prefix = []

# -- Options for HTML output ---------------------------------------------------

html_theme = 'default'
#html_theme_options = {}
#html_theme_path = []
#html_title = None
#html_short_title = None
#html_logo = None
#html_favicon = None
html_static_path = ['_static']
#html_last_updated_fmt = '%b %d, %Y'
#html_use_smartypants = True
#html_sidebars = {}
#html_additional_pages = {}
#html_domain_indices = True
#html_use_index = True
#html_split_index = False
#html_show_sourcelink = True
#html_show_sphinx = True
#html_show_copyright = True
#html_use_opensearch = ''
#html_file_suffix = None
htmlhelp_basename = '%sdoc' % picroscopy.__name__

# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '10pt',
    #'preamble': '',
}

latex_documents = [
    (
        'index',                          # source start file
        '%s.tex' % picroscopy.__name__,   # target filename
        '%s Documentation' % project,     # title
        picroscopy.__author__,            # author
        'manual',                         # documentclass
        ),
]

#latex_logo = None
#latex_use_parts = False
#latex_show_pagerefs = False
#latex_show_urls = False
#latex_appendices = []
#latex_domain_indices = True

# -- Options for manual page output --------------------------------------------

man_pages = [
    (
        'index',                          # source start file
        picroscopy.__name__,              # page name
        '%s Documentation' % project,     # description
        [picroscopy.__author__],          # author list
        1,                                # manual section
        ),
]

#man_show_urls = False

# -- Options for Texinfo output ------------------------------------------------

texinfo_documents = [
    (
        'index',                          # source start file
        picroscopy.__name__,              # target name
        '%s Documentation' % project,     # title
        picroscopy.__author__,            # author
        project,                          # dir menu entry
        picroscopy.__doc__,               # description
        'Miscellaneous',                  # category
        ),
]

#texinfo_appendices = []
#texinfo_domain_indices = True
#texinfo_show_urls = 'footnote'
#texinfo_no_detailmenu = False

