""" Copy Dialog Branch Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

copy_dialog_data: Copy dialog nodes from a source WCS workspace to a
    target workspace
"""

from datetime import datetime
from typing import Tuple

import anytree
from anytree.iterators.levelorderiter import LevelOrderIter

from .._constants import _DEFAULT_BACKUP_FILE
from ..util.get_and_backup_workspace import get_and_backup_workspace
from ._util import (
    _build_tree,
    _get_branch_node,
    _insert_into_target_tree,
    _get_all_matches,
    _get_nodes_with_jump,
    _get_matcher_function,
    _sort_child_nodes,
    _update_workspace
    )

def copy_dialog_branch(
        root_node: str = '',
        target_node: str = 'root',
        target_insert_as: str = 'child',
        source_username: str = '',
        source_password: str = '',
        source_workspace: str = '',
        target_username: str = '',
        target_password: str = '',
        target_workspace: str = '',
        version: str = '',
        target_backup_file: str = _DEFAULT_BACKUP_FILE) -> \
            Tuple[anytree.AnyNode, str]:
    """ Copy a dialog branch (and any jumps) to a target workspace at
    `target_node` using `target_insert_as` strategy (child, last_child,
    or sibling). Writes a backup of the target workspace to
    `target_backup_file`

    Root
    |
    |--Target Node
    |       |
    |       |<-(insert as child)
    |       |
    |       |--Existing Node
    |       |
    |       |<-(insert as last_child)
    |       |
    |       |--"true" node
    |
    |<-(insert as sibling)
    |
    ...

    parameters:
    root_node: ID or title of the root node in source
    target_node: ID or title of the root node in target
    target_insert_as: Default 'child'. Location of branch insertion, with
        respect to the target node. valid options ['child', 'last_child'
        or 'sibling']
    source_username: Username for source WCS instance
    source_password: Password for source WCS instance
    source_workspace: Workspace ID for source WCS instance
    target_username: Username for target WCS instance
    target_password: Password for target WCS instance
    target_workspace: Workspace ID for target WCS instance
    version: WCS API version
    target_backup_file: write a backup of target workspace to this file

    returns:
    target_nodes: the root node of the projected target tree
    projected: a string representation of the projected tree
    """

    #validate that values are provided
    args = locals()
    for key in [
            'root_node',
            'target_node',
            'target_insert_as',
            'source_username',
            'source_password',
            'source_workspace',
            'target_username',
            'target_password',
            'target_workspace',
            'version',
            'target_backup_file']:
        if args[key] is '':
            raise ValueError("Argument '{}' requires a value".format(key))

    # can't copy the entire root
    if root_node == 'root' or root_node is None:
        raise ValueError("""Root node cannot be the source root.
                            Import the workspace instead.""")
    # need a valid insert type
    target_insert_as = target_insert_as.lower()
    if target_insert_as not in ['child', 'last_child', 'sibling']:
        raise ValueError("""'target_insert_as is required to be one of
                            'child', 'last_child', or 'sibling'""")

    # build backup file if not specified
    # otherwise just call it the POSIX timestamp
    if target_backup_file == _DEFAULT_BACKUP_FILE:
        target_backup_file = _DEFAULT_BACKUP_FILE.format(
            str(datetime.now().timestamp()))

    # set root references to None for consistency
    if target_node == 'root':
        target_node = None

    # we will need to walk up the trees
    tree_walker = anytree.walker.Walker()

    # get export of workspaces
    source_export = get_and_backup_workspace(
        username=source_username,
        password=source_password,
        version=version,
        workspace=source_workspace,
        export_path=target_backup_file)

    target_export = get_and_backup_workspace(
        username=target_username,
        password=target_password,
        version=version,
        workspace=target_workspace,
        export_path=None)

    # build tree roots
    source_nodes = anytree.AnyNode(id=None, title=None, desc='root')
    target_nodes = anytree.AnyNode(id=None, title=None, desc='root')

    # build our trees
    _build_tree(source_export['dialog_nodes'], source_nodes)
    _build_tree(target_export['dialog_nodes'], target_nodes)

    # we only have one value for these branches
    source_branch = _get_branch_node(source_nodes, root_node, 'source')
    target_branch = _get_branch_node(target_nodes, target_node, 'target')

    # we need to have ensure branches in order to insert
    if source_branch is None:
        raise RuntimeError('No matching root node found in source')
    if target_branch is None:
        raise RuntimeError('No target node found in target')

    # insert a copy of the source branch into the target tree
    _insert_into_target_tree(
        source_branch,
        target_branch,
        target_nodes,
        target_insert_as)

    # check for any jumps, these will need to be accounted for
    nodes_with_jumps = anytree.search.findall(
        source_branch,
        filter_=_get_nodes_with_jump)

    # this is the set of nodes that jumped to
    to_jump_to = [x.node['next_step']['dialog_node'] \
        for x in nodes_with_jumps]


    # make sure that we have a valid destination for the jump
    # if not, we will insert at the first common ancestor
    for jump_id in to_jump_to:
        # destination exists, move on
        jump_node = anytree.search.findall(
            target_nodes,
            filter_=_get_matcher_function(jump_id))

        if jump_node:
            continue

        # we need to find the common ancestor
        source_branch = _get_branch_node(source_nodes, jump_id, 'source')

        if source_branch is None:
            raise RuntimeError('No matching jump node found in source')

        ancestors, _, _ = tree_walker.walk(source_branch, source_nodes)

        # assume we need to insert at the root (the last ancestor as we walk
        # up the tree)
        common_ancestor = ancestors[-1]
        for node in ancestors:
            # otherwise, if we have found a common ancestor, we can insert at
            # that point
            if _get_branch_node(target_nodes, node.id, 'target') is not None:
                common_ancestor = node
                continue

        # set our insert point
        target_branch = target_nodes
        if common_ancestor.parent.id is not None:
            target_branch = _get_branch_node(
                target_nodes,
                common_ancestor.id,
                'target')

        # insert the jump to information
        # will always be done as last child
        _insert_into_target_tree(
            common_ancestor,
            target_branch,
            target_nodes,
            'last_child')

        # find any new jumps
        nodes_with_jumps = anytree.search.findall(
            common_ancestor,
            filter_=_get_nodes_with_jump)

        # add these new jumps to be checked
        for node in nodes_with_jumps:
            to_jump_to.append(node.node['next_step']['dialog_node'])

    # for rendering, let's update the desc fields with titles of the jump
    nodes_with_jumps = anytree.search.findall(
        target_nodes,
        filter_=_get_nodes_with_jump)

    # update the descriptions
    for node in nodes_with_jumps:
        dest = _get_all_matches(
            target_nodes,
            node.node['next_step']['dialog_node'])
        if len(dest) == 1:
            node.desc = node.desc + ' (jumps to: {})'.format(dest[0].desc)

    # go ahead and update the workspace
    _update_workspace(
        target_username,
        target_password,
        target_workspace,
        [x.node for x in LevelOrderIter(target_nodes) \
            if x.id is not None])
    print('\n\ndialog update complete')

    # projected rendering of tree
    projected = anytree.RenderTree(
        target_nodes,
        childiter=_sort_child_nodes).by_attr(attrname='desc')

    return target_nodes, projected
