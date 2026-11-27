# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Growbies Owner's Manual"
author = 'Growbies, LLC'# noinspection PyShadowingBuiltins
copyright = '2026, Growbies'
release = '1.0.17'

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
        # 'sidebar/brand.html',
        'sidebar/search.html',
        'sidebar/navigation.html',
    ],
}


html_static_path = ['_static']

html_css_files = [
    'custom.css',
]

latex_elements = {
    'classoptions': ',openany,oneside',
}
latex_theme = 'howto'

# --- Sphinx Multiversion
# Only build firmware documentation branches.
# Ignore git tags
smv_tag_whitelist = ''

# Include branches from origin.
smv_remote_whitelist = None

# Put each revision in its own output directory.
smv_outputdir_format = '{ref.name}'

templates_path = ['_templates']
