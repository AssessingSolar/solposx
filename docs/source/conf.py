# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
from pathlib import Path
import importlib
import inspect
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------

project = 'solposx'
copyright = '2025 Adam R. Jensen'
author = 'Adam R. Jensen, Kevin S. Anderson, & Ioannis Sifnaios'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'myst_nb',  # markdown and jupyter-notebook parsing
    'sphinx.ext.autodoc',  # generate documentation from docstrings
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',  # parsing of Numpy docstrings
    'sphinx.ext.extlinks',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = "sphinx_book_theme"
html_title = "solposx"
# html_logo = "_static/solposx_logo.svg"
# html_favicon = "_static/solposx_logo.svg"

# https://sphinx-book-theme.readthedocs.io/en/stable/reference.html
html_theme_options = {
    "repository_url": "https://github.com/assessingsolar/solposx",
    "path_to_docs": "docs/source/",
    "use_issues_button": True,
    "use_repository_button": True,
    "use_download_button": False,
    "use_edit_page_button": True,

    # layout structure config options inherited from pydata-sphinx-theme
    # https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/layout.html
    "secondary_sidebar_items": ["page-toc", "edit-this-page"]
}
html_css_files = [
    'css/fix-horizontal-sidebar-elements.css',
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),
    "pvlib": ("https://pvlib-python.readthedocs.io/en/stable/", None),
}

extlinks = {
    "issue": ("https://github.com/assessingsolar/solposx/issues/%s", "GH%s"),
    "pull": ("https://github.com/assesingsolar/solposx/pull/%s", "GH%s"),
    "ghuser": ("https://github.com/%s", "@%s"),
    "doi": ("http://dx.doi.org/%s", "DOI: %s"),
}


# Number of seconds for a cell to execute before timeout (default=30)
nb_execution_timeout = 120


# helper functions for intelligent "View on Github" links
# based on
# https://gist.github.com/flying-sheep/b65875c0ce965fbdd1d9e5d0b9851ef1

# select correct base URL depending on the build system context
def get_source_base_url():
    """
    Get the base URL for the source code to generate links to GitHub source.
    If the build is on ReadTheDocs and it's a stable version, use the
    versioned link. If it's a latest version, use the main link.

    For other builds (e.g. pull requests), use the main link.
    Local builds will also use the main link.

    Resulting base URL should end with a trailing slash.

    See https://docs.readthedocs.com/platform/stable/reference/environment-variables.html
    """
    repo_url = os.environ.get(
        "READTHEDOCS_GIT_CLONE_URL",
        default="https://github.com/AssessingSolar/solposx",
    )
    READTHEDOCS_ENV = os.environ.get("READTHEDOCS", None) == "True"
    READTHEDOCS_VERSION = os.environ.get("READTHEDOCS_VERSION", None)
    READTHEDOCS_GIT_IDENTIFIER = os.environ.get(
        "READTHEDOCS_GIT_IDENTIFIER", None
    )
    if READTHEDOCS_ENV:  # Building docs on ReadTheDocs
        if READTHEDOCS_VERSION == "latest":  # latest version, commited to main
            repo_url += "/blob/main/"
        elif READTHEDOCS_VERSION == "stable":  # stable version, has a tag
            repo_url += f"/blob/{READTHEDOCS_GIT_IDENTIFIER}/"
        else:  # pull request, user and branch are unknown so use main
            repo_url += "/blob/main/"
    else:  # Local build
        repo_url += "/blob/main/"  # can't tell where to point to
    return repo_url


def get_linkable_source_object(qualname):
    """
    Get a module/class/attribute and its original module by qualname.

    Useful for looking up the original location when a function is imported
    into an __init__.py

    Examples
    --------
    >>> source_object = get_linkable_source_object("solposx.refraction.archer")
    >>> source_object
    <function solposx.refraction.archer.archer(elevation)>
    >>> inspect.getsourcelines(source_object)[1]
    5
    """
    try:  # assume a python function fully qualified name
        module_name, obj_func_name = qualname.rsplit('.', maxsplit=1)
        mod = importlib.import_module(module_name)
        obj = getattr(mod, obj_func_name)
    except ModuleNotFoundError:  # module_name does not make for a module
        # assume it's a class definition
        module_name, class_name, attribute_name = qualname.rsplit(".", maxsplit=2)
        class_obj = get_linkable_source_object(f"{module_name}.{class_name}")
        try:  # let's try to get the attribute
            # fails if it's set dynamically
            attribute_obj = getattr(class_obj, attribute_name)
        except Exception:  # noqa: BLE001
            obj = class_obj
        else:
            try:  # try to find the source lines
                # if not a code object, it fails
                inspect.getsourcelines(attribute_obj)
            except TypeError:
                # return the class if code lines are not available
                obj = class_obj
            else:
                obj = attribute_obj
    return obj


def get_linenos(obj):
    """Get object start/end line numbers in its source code file."""
    try:
        lines, start = inspect.getsourcelines(obj)
    except Exception:  # noqa: BLE001
        # fallback
        return None, None
    else:
        return start, start + len(lines) - 1

URL_BASE = get_source_base_url()  # Edit on GitHub source code base link
REPO_ROOT_DIR = Path.cwd().parent.parent  # sphinx's cwd is where conf.py resides

def make_github_url(file_name):
    """
    Generate the appropriate GH link for a given docs page.  This function
    is intended for use in sphinx template files.

    The target URL is built differently based on the type of page.  The pydata
    sphinx theme has a built-in `file_name` variable that looks like
    - "index.md"
    - "tools.rst"
    - "generated/solposx.tools.calc_error.rst"
    """
    file_name = Path(file_name)  # ease manipulation
    # is it an API autogen page?
    if "generated" in file_name.parts:
        qualname = file_name.stem
        obj = get_linkable_source_object(qualname)
        path = Path(inspect.getfile(obj))
        target_url = URL_BASE + str(path.relative_to(REPO_ROOT_DIR))
        # add line numbers if meaningful
        if inspect.isfunction(obj) or inspect.isclass(obj) or inspect.ismethod(obj):
            start, end = get_linenos(obj)
            if start and end:
                target_url += f'#L{start}-L{end}'

    # Just any other source file, as is, either .rst, .ipynb or .md.
    else:
        target_url = URL_BASE + "docs/source/" + str(file_name)

    return target_url

# variables to pass into the HTML templating engine; these are accessible from
# _templates/breadcrumbs.html
html_context = {
    'make_github_url': make_github_url,
    'edit_page_url_template': '{{ make_github_url(file_name) }}',
}
