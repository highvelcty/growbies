# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'Growbies Gateway'

# noinspection PyShadowingBuiltins
copyright = '2026, Growbies, LLC'

author = 'Growbies, LLC'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
default_dark_mode = True

extensions = ['sphinx_multiversion']

html_sidebars = {
    '**': [
        'versioning.html',
        'sidebar/search.html',
        'sidebar/navigation.html',
    ],
}


html_static_path = ['_static']

html_css_files = [
    'custom.css',
]

# --- Sphinx Multiversion
# discovery - remote branches only. Disregard tags and local branches
smv_remote_whitelist = '^origin$'
smv_branch_whitelist= ''
smv_tag_whitelist = ''

# Put each revision in its own output directory.
smv_outputdir_format = '{ref.name}'

templates_path = ['_templates']
