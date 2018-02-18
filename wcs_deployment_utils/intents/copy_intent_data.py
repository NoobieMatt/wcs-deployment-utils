""" Copy Intent Data Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

copy_intent_data: copies intent data from a source workspace
"""
from datetime import datetime
import pandas as pd
from watson_developer_cloud import ConversationV1, WatsonException
from ..util.get_and_backup_workspace import get_and_backup_workspace
from ._util import _load_intent_data
from .._constants import _DEFAULT_BACKUP_FILE

def copy_intent_data(intent: str = None,
                     source_username: str = None,
                     source_password: str = None,
                     source_workspace: str = None,
                     target_username: str = None,
                     target_password: str = None,
                     target_workspace: str = None,
                     version: str = None,
                     clear_existing: bool = False,
                     target_backup_file: str = _DEFAULT_BACKUP_FILE) -> None:
    """ Copy intent data from a WCS workspace

    Copy intent data in an additive pattern from a source workspace
    to a target workspace. copy is additive with existing
    data and will not replace existing data unless clear_existing is
    specified

    parameters:
    intent: name of intent to copy
    source_username: username for source WCS instance
    source_password: password for source WCS instance
    source_workspace: workspace id for source WCS instance
    target_username: username for target WCS instance
    target_password: password for target WCS instance
    target_workspace: workspace id for target WCS instance
    version: version of WCS instances
    clear_existing: boolean to clear existing intent data from target
    target_backup_file: backup existing target workspace to this file
    """

    # validate that values are provided
    args = locals()
    for key in [
            'intent',
            'source_username',
            'source_password',
            'source_workspace',
            'target_username',
            'target_password',
            'target_workspace',
            'version']:
        if args[key] is None:
            raise ValueError("Argument '{}' requires a value".format(key))

    # build backup file if not specified
    # otherwise just call it the POSIX timestamp
    if target_backup_file == _DEFAULT_BACKUP_FILE:
        target_backup_file = _DEFAULT_BACKUP_FILE.format(
            str(datetime.now().timestamp()))

    # backup our target instance
    _ = get_and_backup_workspace(
        username=target_username,
        password=target_password,
        workspace=target_workspace,
        version=version,
        export_path=target_backup_file)

    # setup conversation class
    target_conv = ConversationV1(
        username=target_username,
        password=target_password,
        version=version
    )

    source_conv = ConversationV1(
        username=source_username,
        password=source_password,
        version=version
    )

    # load data
    try:
        intent_data_res = source_conv.get_intent(
            workspace_id=source_workspace,
            intent=intent,
            export=True
        )
    except WatsonException:
        raise ValueError("Unable to read source intent")

    intent_examples = []
    for example in intent_data_res['examples']:
        intent_examples.append(example['text'])

    intent_data = pd.DataFrame(data={
        "action": ['ADD'] * len(intent_examples),
        "intent": [intent] * len(intent_examples),
        "example": intent_examples
    })

    config_data = {
        "clear_existing": clear_existing
    }

    # call the function
    _load_intent_data(conversation=target_conv,
                      workspace_id=target_workspace,
                      intent_data=intent_data,
                      config_data=config_data)

    print("copy_intent_data for '{}' complete.".format(intent))
