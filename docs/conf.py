import os
import sys

from sphinx_gallery.sorting import FileNameSortKey

sys.path.insert(0, os.path.abspath(".."))

import pandera_catalog

# -- Project information -----------------------------------------------------

project = "pandera-catalog"
copyright = "2026, Greg Elphick"
author = "Greg Elphick"
version = pandera_catalog.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    'sphinx_gallery.gen_gallery',  # to generate a gallery of examples
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx.ext.todo",
]

todo_include_todos = True
autosummary_generate = True

sphinx_gallery_conf = {
    'filename_pattern': r'\.py',
    'ignore_pattern': r'(__init__)|(xx.*)\.py',
    'examples_dirs': '../examples',  # path to your example scripts
    'gallery_dirs': 'auto_examples',  # path to where to save gallery generated output
    'within_subsection_order': FileNameSortKey,
    'capture_repr': ('_repr_html_', '__repr__'),
    'image_scrapers': ["matplotlib"],
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_title = "pandera-catalog Documentation"

html_logo = "_static/branding/pandera-catalog.svg"
html_favicon = "_static/branding/pandera-catalog.svg"

html_theme_options = {
    "repository_url": "https://github.com/elphick/pandera-catalog",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "docs",
    "repository_branch": "main",
    "logo": {
        "image_light": "_static/branding/pandera-catalog.svg",
        "image_dark": "_static/branding/pandera-catalog.svg",
        "text": f"pandera-catalog<br>({version})",
    },
}

html_css_files = ["custom.css"]
