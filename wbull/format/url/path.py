"""URL path manipulation.

This module provides methods to manipulate paths in URLs.
"""

import collections
import fnmatch
import posixpath
import re


def is_subdir(parent_path: str, child_path: str, wildcards: bool=False) \
        -> bool:
    """Return whether a path is a subdirectory of another.

    Args:
        child_path: The path being tested which may be a subdirectory.
        parent_path: The path which may contain the path being tested.
        wildcards: If True, globbing wildcards can be used in
            `parent_path` and are matched against `child_path`.
    """
    child_dir = posixpath.dirname(child_path)
    parent_dir = posixpath.dirname(parent_path)
    child_dir_parts = child_dir.split('/')
    parent_dir_parts = parent_dir.split('/')

    if len(parent_dir_parts) > len(child_dir_parts):
        # child path is already outside parent
        return False

    if wildcards:
        return all(fnmatch.fnmatchcase(child_part, parent_part)
                   for parent_part, child_part
                   in zip(parent_dir_parts, child_dir_parts)
                   )
    else:
        return all(parent_part == child_part
                   for parent_part, child_part
                   in zip(parent_dir_parts, child_dir_parts)
                   )


def flatten_path(path: str, flatten_slashes: bool=False):
    """Flatten an URL path by removing the dot segments.

    Arguments:
        path: The URL path.
        flatten_slashes: Whether to replace consecutive/duplicate
            slashes with a single slash. Removal is done after dot
            segments are processed.

    Dot segments are notational forms resembling relative paths in
    filesystems. A single period (`.`) between slashes indicates the
    current directory and two periods (`..`) indicates the parent
    directory. Flattening paths are recommended to avoid representing
    the same resource in infinite ways.

    Consecutive slashes are semantically different from a single slash
    but they often point to the same resource. As such, flattening
    them is suggested.

    The builtin function :func:`urllib.parse.urljoin` has some support
    for removing dot segments, but it is conservative and only removes
    them as needed.

    If the resulting path is empty, an empty string is returned. This
    is syntactically different from a single slash but is semantically
    the same in URLs. You may want to normalize the empty string to a
    single slash.
    """
    parts = path.split('/')
    new_parts = collections.deque()

    for part in parts:
        if part == '.':
            continue
        elif part != '..':
            new_parts.append(part)
        elif new_parts:
            new_parts.pop()

    new_path = '/'.join(new_parts)

    if flatten_slashes:
        new_path = re.sub(r'/+', '/', new_path)

    return new_path
