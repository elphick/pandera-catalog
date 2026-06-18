import os
import sys

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
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",
    "sphinx.ext.todo",
]

todo_include_todos = True
autosummary_generate = True

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
