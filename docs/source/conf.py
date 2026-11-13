# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Growbies'

# noinspection PyShadowingBuiltins
copyright = '2026, Eric Meyer'

author = 'Eric Meyer'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
default_dark_mode = True

extensions = ['sphinx_multiversion']

# --- Sphinx Multiversion
# Only build firmware documentation branches.
smv_branch_whitelist = r'^docs/gateway-.*$'

# Ignore git tags
smv_tag_whitelist = ''

# Include branches from origin.
smv_remote_whitelist = r'^origin$'

# Put each revision in its own output directory.
smv_outputdir_format = '{ref.name}'
