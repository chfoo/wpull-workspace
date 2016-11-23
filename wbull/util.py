# import itertools
#
#
# def grouper(iterable, n, fillvalue=None):
#     "Collect data into fixed-length chunks or blocks"
#     # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
#     # From itertool recipies
#     args = [iter(iterable)] * n
#     return itertools.zip_longest(*args, fillvalue=fillvalue)
import os
import sys

from typing import Optional


def get_package_data_path(filename: str, package_dir: Optional[str]=None) -> str:
    """Return the path of a package data file.

    :see_also: :func:`pkgutil.get_data`
    """
    if getattr(sys, 'frozen', False):
        package_dir = os.path.join(
            sys._MEIPASS,
            os.path.basename(os.path.dirname(__file__))
        )
    elif not package_dir:
        package_dir = os.path.dirname(__file__)

    return os.path.join(package_dir, filename)


def get_exception_message(instance: Exception) -> str:
    """Try to get the exception message or the class name."""
    args = getattr(instance, 'args', None)

    if args:
        return str(instance)

    try:
        return type(instance).__name__
    except AttributeError:
        return str(instance)
