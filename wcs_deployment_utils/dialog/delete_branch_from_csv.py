""" Delete Dialog Branch Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

delete_branch_from_csv: Delete branches as specified as in a CSV file
"""

from datetime import datetime
from typing import Tuple, List
import pandas as pd
from watson_developer_cloud import ConversationV1, WatsonException
from ._util import _find_node
from ..util.get_and_backup_workspace import get_and_backup_workspace

from .._constants import _DEFAULT_BACKUP_FILE

def delete_branch_from_csv(
        conversation_username: str = '',
        conversation_password: str = '',
        version: str = '',
        workspace: str = '',
        csv_file: str = '',
        target_backup_file: str = _DEFAULT_BACKUP_FILE) -> \
            Tuple[List[Tuple], List[Tuple]]:
    """ Iterate through a CSV file and prune dialog tree
    A backup will be kept at `target_backup_file`

    CSV file will be of the following structure:
    action,id

    valid actions are "REMOVE"

    id will refer to either a node ID or a node title

    parameters:
    conversation_username: username for WCS instance
    conversation_password: password for WCS instance
    version: version of WCS API
    workspace: workspace for WCS instance
    csv_file: csv file containing branches to remove
    target_backup_file: backup workspace at this path

    returns:
    nodes_removed: list of (identifier, id) s of nodes removed
    nodes_not_existing: list of identifiers of nodes not found in target
    """

    #validate that values are provided
    args = locals()
    for key in [
            'conversation_username',
            'conversation_password',
            'version',
            'workspace',
            'csv_file']:
        if args[key] is '':
            raise ValueError("Argument '{}' requires a value".format(key))

    # build backup file if not specified
    # otherwise just call it the POSIX timestamp
    if target_backup_file == _DEFAULT_BACKUP_FILE:
        target_backup_file = _DEFAULT_BACKUP_FILE.format(
            str(datetime.now().timestamp()))

    # setup conversation class
    conversation = ConversationV1(
        username=conversation_username,
        password=conversation_password,
        version=version
    )

    # get and backup our target instance
    dialog_export = get_and_backup_workspace(
        username=conversation_username,
        password=conversation_password,
        workspace=workspace,
        version=version,
        export_path=target_backup_file
    )

    # load data
    dialog_data = pd.read_csv(
        csv_file,
        dtype='str',
        keep_default_na=False)

    nodes_removed = []
    nodes_not_existing = []

    # handle removes
    rows_to_remove = dialog_data[dialog_data['action'] == 'REMOVE']
    for _, row in rows_to_remove.iterrows():
        try:
            # locate the node to remove
            node_to_remove = _find_node(
                row['id'],
                dialog_export['dialog_nodes'])
            if node_to_remove is None:
                print(("Unable to locate node '{}'. "
                       "It may have already been removed.").format(
                           row['id']))
                # identifier was never in workspace
                nodes_not_existing.append(row['id'])
                continue
            # delete this node
            conversation.delete_dialog_node(
                workspace_id=workspace,
                dialog_node=node_to_remove['dialog_node'])
            nodes_removed.append(
                (row['id'],
                 node_to_remove['dialog_node']))
        except WatsonException:
            try:
                # check if it even exists
                conversation.get_dialog_node(
                    workspace_id=workspace,
                    dialog_node=node_to_remove['dialog_node'])
                # if it exists and we could not delete it
                # the operation has failed
                print("Unable to delete node '{}'. ".format(
                    row['id']))
                raise RuntimeError('Unable to delete node {}'.format(
                    row['id']))
            except WatsonException:
                # Node doesn't exist. Nothing to do
                nodes_removed.append(
                    (row['id'],
                     node_to_remove['dialog_node']))
    print("delete_branch_from_csv complete for {}".format(csv_file))
    return nodes_removed, nodes_not_existing
