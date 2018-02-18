""" Get and Backup Workspace Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

get_and_backup_workspace: Copy dialog nodes from a source WCS workspace to a
    target workspace
"""

from typing import Union
from os import makedirs, path
import json

from watson_developer_cloud import ConversationV1

def get_and_backup_workspace(username: str = None,
                             password: str = None,
                             workspace: str = None,
                             version: str = None,
                             export_path: Union[str, None] = None) -> dict:
    """ Gets an export of a workspace and stores it locally

    parameters:
    username: WCS username
    password: WCS password
    workspace: WCS workspace id
    version: WCS API version
    export_path: store export at this path
    """
    # build Conversation SDK object
    conv = ConversationV1(
        username=username,
        password=password,
        version=version
    )

    # get export of workspaces
    export = conv.get_workspace(
        workspace_id=workspace,
        export=True)

    if export_path is not None:
        # make the directories if needed
        makedirs(path.dirname(export_path), exist_ok=True)
        with open(export_path, mode='w') as export_file:
            json.dump(export, export_file)

    return export
