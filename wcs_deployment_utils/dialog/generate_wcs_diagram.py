""" Generate WCS Diagram Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

generate_wcs_diagram: generates a text based diagram of a WCS workspace.
"""

import anytree

from ._util import (
    _build_tree,
    _sort_child_nodes,
    _get_nodes_with_jump,
    _get_all_matches)
from ..util.get_and_backup_workspace import get_and_backup_workspace

def generate_wcs_diagram(
        conversation_username: str = None,
        conversation_password: str = None,
        version: str = None,
        workspace: str = None) -> str:
    """ generates a compact, text represation of a WCS instance.
    ex:

    root
    ├── welcome
    ├── 1 (jumps to: 3)
    ├── 2
    │   ├── 2_1
    │   └── 2_2
    ├── 3
    │   ├── 3_1
    │   ├── 3_2
    │   └── 3_3
    └── Anything else

    parameters:
    conversation_username: WCS instance username
    conversation_password: WCS instance password
    version: WCS API version
    workspace: WCS instance workspace

    returns:
    projection: a string representation of the WCS workspace
    """

    export = get_and_backup_workspace(
        username=conversation_username,
        password=conversation_password,
        version=version,
        workspace=workspace,
        export_path=None)

    # build tree roots
    root = anytree.AnyNode(id=None, title=None, desc='root')

    # build our trees
    _build_tree(export['dialog_nodes'], root)

    # for rendering, let's update the desc fields with titles of the jump
    nodes_with_jumps = anytree.search.findall(
        root,
        filter_=_get_nodes_with_jump)

    # update the descriptions
    for node in nodes_with_jumps:
        dest = _get_all_matches(
            root,
            node.node['next_step']['dialog_node'])
        if len(dest) == 1:
            node.desc = node.desc + ' (jumps to: {})'.format(dest[0].desc)

    # projected rendering of tree
    projected = anytree.RenderTree(
        root,
        childiter=_sort_child_nodes).by_attr(attrname='desc')

    return projected
