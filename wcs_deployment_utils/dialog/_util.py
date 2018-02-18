""" Utility functions for dialog package
"""

from queue import Queue
from copy import deepcopy
from typing import List, Union
from types import FunctionType
from warnings import warn

import requests
import anytree
from anytree import AnyNode
from anytree.iterators.levelorderiter import LevelOrderIter

from .._constants import _BASE_WCS_ENDPOINT

# TREE BUILDING FUNCTIONS
# WCS Exports -> AnyTree instances

def _build_tree(nodes: List[dict], root: AnyNode) -> None:
    """ Build a tree from a list of dialog nodes from a WCS export beginning
    from root

    parameters:
    nodes: list of dialog nodes from a WCS workspace export
    root: root node for tree
    """
    parents = Queue()
    parents.put(root)

    while not parents.empty():
        # get our parent
        parent = parents.get()
        # find their children from the array returned from WCS
        children = _find_children(parent.id, nodes)
        for child in children:
            # add the children and then add them to the parents queue
            if child['title'] is not None:
                desc = child['title']
            elif child['conditions'] is not None:
                desc = child['conditions']
            else:
                desc = 'no label'
            if child['type'] not in ['standard', 'frame']:
                if child['conditions'] is not None:
                    desc = child['type'] + ' - ' + child['conditions']
                else:
                    desc = child['type']
            parents.put(
                AnyNode(parent=parent,
                        id=child['dialog_node'],
                        title=child['title'],
                        node=child,
                        desc=desc)
            )

def _find_first_node(dialog_nodes: List[dict]) -> dict:
    """ Find the first node evaluated in a WCS dialog flow (first child of
    dialog root)

    parameters:
    dialog_nodes: list of dialog nodes from a WCS workspace export

    returns:
    dialog_node: the first dialog node in execution order (top left)
    """
    for node in dialog_nodes:
        if (node['parent'] is None and
                node['previous_sibling'] is None):
            return node

def _find_children(node_id: str, dialog_nodes: List[str]) -> str:
    """ Find the children of a specified node id in an array of dialog nodes

    parameters:
    node_id: The ID or title of the dialog node
    dialog_nodes: The list of dialog nodes to search on

    Returns:
    children: List of nodes that are children of the node_id
    """

    children = []

    for node in dialog_nodes:
        # It will match either the node title or the id
        if node['parent'] == node_id:
            children.append(node)

    return children

# TREE UTILITY FUNCTIONS
# Interacting with AnyTree instances

def _insert_into_target_tree(
        source_root: AnyNode,
        target_node: AnyNode,
        target_tree_root: AnyNode,
        insert_type: str) -> None: # Dict[str, dict]:
    """ Inserts the source root at the target root by insert type

    parameters:
    source_root: Tree node to copy into target
    target_node: Insert source at this node
    target_tree_root: root node for target
    target_tree: dict of nodes from the target (to validate relationships)
    insert_type: 'child', 'sibling', 'last_child' insert method


    Returns:
    inserted_nodes: dict of inserted nodes as dict['id'] = node
    """
    # remove any prior references to the id
    for node in LevelOrderIter(source_root):
        # can't remove the root node
        if node.id is None:
            continue
        existing = _get_all_matches(target_tree_root, node.id)
        for ex in existing:
            previous_sibling = _get_previous_sibling(ex)
            next_sibling = _get_next_sibling(ex)
            ex.parent = None
            # if there's no next sibling, nothing to update
            if not next_sibling:
                continue
            # removed node was a first child
            if previous_sibling is None:
                next_sibling.node['previous_sibling'] = None
            else:
                next_sibling.node['previous_sibling'] = \
                    previous_sibling.id

    # verify that we have not removed the target node by nature of clearing
    # out colliding nodes

    if not _get_all_matches(target_tree_root, target_node.id):
        raise RuntimeError("""target node has been removed
                              when pruning source collisions""")

    # copy the source branch
    source_copy = deepcopy(source_root)
    if insert_type not in ['child', 'last_child', 'sibling']:
        insert_type = 'child'
        warn('invalid insert_type, defaulting to child', Warning)

    # we can only insert a child to the root node
    if target_node.parent is None:
        if insert_type not in ['child', 'last_child']:
            insert_type = 'child'
            warn('only "child" and "last_child" inserts are ' \
                'available when targeting root. Using child.', Warning)

    # child
    # parent = target
    # previous_sibling = None
    if insert_type == 'child':
        displaced = _get_first_child(target_node)
        if displaced is not None:
            displaced.node['previous_sibling'] = source_copy.id
        source_copy.parent = target_node
        source_copy.node['parent'] = target_node.id
        source_copy.node['previous_sibling'] = None

    # last_child
    # parent = target
    # previous_sibling = last non-true sibling
    elif insert_type == 'last_child':
        # current last child (None if there is no last child)
        last_child = _get_last_nontrue_child(target_node)
        # node to be displaced
        displaced = _get_next_sibling(last_child)
        # if we have displaced a node, we must shift it's previous sibling
        if displaced is not None:
            displaced.node['previous_sibling'] = source_copy.id

        source_copy.parent = target_node
        source_copy.node['parent'] = target_node.id
        if last_child is None:
            source_copy.node['previous_sibling'] = None
        else:
            source_copy.node['previous_sibling'] = last_child.id

    # sibling
    # parent = target.parent
    # previous_sibling = target
    elif insert_type == 'sibling':
        displaced = _get_next_sibling(target_node)
        # shift the potentially displaced node
        if displaced is not None:
            displaced.node['previous_sibling'] = source_copy.id

        source_copy.parent = target_node.parent
        source_copy.node['parent'] = target_node.node['parent']
        source_copy.node['previous_sibling'] = \
            target_node.id

def _get_matcher_function(identifier: str, id_only: bool = True) -> FunctionType:
    """ Returns a function that will match nodes on a given identifier
    Depending on the node configuration, it will match on id and if present,
    title.

    parameters:
    identifier: identifier to match on
    id_only: (True) Match on id only or id and title

    Returns:
    children: List of nodes that are children of the node_id
    """
    # if id is a string, match it against title and id if available
    if isinstance(identifier, str):
        def function(node): # pylint: disable=C0111
            if node.id is None or id_only:
                return node.id == identifier
            elif isinstance(node.title, str):
                return (node.title.lower() == identifier.lower() or
                        node.id.lower() == identifier.lower())
            else:
                return node.id.lower() == identifier.lower()
    # otherwise, the only match is on id. we will not return all nodes with
    # no titles
    else:
        # if not a string, it's None. Since id cannot be None, this can only
        # match a null title
        def function(node): # pylint: disable=C0111
            return node.id == identifier
    return function

def _get_nodes_with_jump(node: AnyNode) -> bool:
    """ Will return true if node contains a jump to. Used in tree searches.

    parameters:
    node: the tree node to inspect

    Returns:
    has_jump: boolean if the node has a jump
    """
    if 'node' not in dir(node):
        return False
    if (node.node['next_step'] is not None and
            node.node['next_step']['behavior'] == 'jump_to'):
        return True
    return False

# TREE TRAVERSAL FUNCTIONS
# Moving around AnyTree nodes

def _get_first_child(node: AnyNode) -> Union[AnyNode, None]:
    """ Returns the first child of a node (parent is None)

    parameters:
    node: reference node

    Returns:
    first_child: first child of reference node
    """
    children = node.children
    for child in children:
        if (child.node['parent'] == node.id and
                child.node['previous_sibling'] is None):
            return child
    return None

def _get_last_nontrue_sibling(node: AnyNode) -> Union[AnyNode, None]:
    """ Returns the last sibling of a node that is not a guaranteed
    true node (conditions are not true or anything_else)

    parameters:
    node: reference node

    Returns:
    last_nontrue_sibling: last non-true sibling of reference node
    """
    last_sibling = node

    while _get_next_sibling(last_sibling) is not None:
        next_sibling = _get_next_sibling(last_sibling)
        if _is_node_simple_true(next_sibling.node):
            break
        last_sibling = next_sibling

    return last_sibling

def _get_next_sibling(node: AnyNode) -> Union[AnyNode, None]:
    """ Returns the next sibling of a node

    parameters:
    node: reference node

    Returns:
    next_sibling: next sibling of the reference node
    """
    if node is None:
        return None

    siblings = node.parent.children
    next_sibling = None

    for sibling in siblings:
        if sibling.node['previous_sibling'] == node.id:
            next_sibling = sibling
            break

    return next_sibling

def _get_previous_sibling(node: AnyNode) -> Union[AnyNode, None]:
    """ Returns the previous sibling of a node

    parameters:
    node: reference node

    Returns:
    previous_sibling: previous sibling of reference node
    """
    if node is None or node.node['previous_sibling'] is None:
        return None

    siblings = node.parent.children
    previous_sibling = None

    for sibling in siblings:
        if node.node['previous_sibling'] == sibling.id:
            previous_sibling = sibling
            break

    return previous_sibling

def _get_last_nontrue_child(node: AnyNode) -> Union[AnyNode, None]:
    """ Returns the last child of a node that is not a guaranteed
    true node (conditions are not true or anything_else)

    parameters:
    node: reference node

    Returns:
    last_child: last non-true child of reference node
    """
    cur = _get_first_child(node)
    return _get_last_nontrue_sibling(cur)

def _get_branch_node(root_node: AnyNode, identifier: Union[str, None], name: str) -> AnyNode:
    """ get a single node for use when identifying branch points. matches titles and ids

    parameters:
    root_node: the root node to search from
    identifier: the title or id to match on

    returns:
    branch_node: the node to branch from
    """
    branch_node = anytree.search.findall(
        root_node,
        filter_=_get_matcher_function(identifier, id_only=False))

    if not branch_node:
        return None
    elif len(branch_node) > 1:
        raise RuntimeError('Found multiple matching nodes in {}'.format(name))

    # we only have one value for these branches
    return branch_node[0]

def _get_all_matches(root_node: AnyNode, identifier: Union[str, None]) -> List[AnyNode]:
    """ get all nodes matching a specified id. should only match one node at a time if
    ids are maintained as unique

    parameters:
    root_node: the root node to search from
    identifier: the id to match on

    returns:
    matched_nodes: the nodes matching the criteria
    """
    matched_nodes = anytree.search.findall(
        root_node,
        filter_=_get_matcher_function(identifier))

    # we only have one value for these branches
    return matched_nodes

def _sort_child_nodes(children: List[AnyNode]) -> List[AnyNode]:
    """ sorts a list of child nodes in the proper order per WCS standards

    params:
    children: list of child nodes
    """
    ordered = []
    if not children:
        return []
    else:
        child = _get_first_child(children[0].parent)
    while child is not None:
        ordered.append(child)
        child = _get_next_sibling(child)
    return ordered

# NODE UTILITIES
# Functions for interacting with tree nodes

def _is_node_simple_true(dialog_node: dict) -> bool:
    """ Returns true if the node is a simple true (conditions are
    true or anything_else)

    parameters:
    dialog_node: WCS dialog node

    Returns:
    simple_true: boolean representing if node is simple true
    """
    if dialog_node['conditions'] is None:
        return False
    return dialog_node['conditions'].lower() in ['true', 'anything_else']

def _find_node(
        identifier: str,
        dialog_nodes: List[dict],
        id_only: bool = False) -> dict:
    """ Find a specific node in an list of dialog node JSON representations

    parameters:
    node_id: The ID or title of the dialog node
    dialog_nodes: The list of DialogNodes to search on
    id_only: Match only on IDs

    Returns:
    target_node: The Dialog Node object for the specified ID or title
    """
    if identifier == 'root':
        return None

    target_node = None

    for node in dialog_nodes:
        # It will match either the node title or the id
        if _is_matching_node(identifier, node, id_only):
            target_node = node
            break

    return target_node

def _is_matching_node(
        identifier: str,
        node: dict,
        id_only: bool = False) -> bool:
    """ returns True if node's id or title match the specified node_id

    parameters:
    identifier: identifier to test against `node`
    node: the dialog node to test
    id_only: only match on the node's id

    Returns:
    is_match: boolean representing if node matches node_id
    """
    if identifier is None:
        return False
    # match only on id
    if id_only or node['title'] is None:
        return node['dialog_node'].lower() == identifier.lower()
    else:
        return (node['dialog_node'].lower() == identifier.lower() or
                node['title'].lower() == identifier.lower())

# WCS API UTILITIES
# Utilities to interact with WCS service

def _update_workspace(
        username: str,
        password: str,
        workspace: str,
        dialog_nodes: List[dict]) -> None:
    """ Updates the target workspace with the list of dialog nodes

    parameters:
    username: WCS username
    password: WCS password
    workspace: WCS workspace id
    dialog_nodes: list of WCS dialog nodes

    """
    res = requests.request(
        "POST",
        _BASE_WCS_ENDPOINT + "workspaces/{}".format(workspace),
        params={
            "version": "2017-05-26",
            "append": "false"},
        json={
            "dialog_nodes": dialog_nodes},
        auth=(username, password))

    if not res.ok:
        print(res.text)
        raise RuntimeError('Dialog update failed')
