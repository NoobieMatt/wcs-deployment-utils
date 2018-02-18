""" Copy Entity Data Module

Part of a set of helper functions to allow Watson Conversation Developers
perform tasks around managing WCS workspaces.

Included in this module are:

copy_entity_data: copies entity data from a source workspace
"""
from datetime import datetime
import pandas as pd
from watson_developer_cloud import ConversationV1, WatsonException
from ..util.get_and_backup_workspace import get_and_backup_workspace
from ._util import _load_entity_data
from .._constants import _DEFAULT_BACKUP_FILE

def copy_entity_data(entity=None,
                     source_username=None,
                     source_password=None,
                     source_workspace=None,
                     target_username=None,
                     target_password=None,
                     target_workspace=None,
                     version=None,
                     clear_existing=False,
                     target_backup_file: str = _DEFAULT_BACKUP_FILE) -> None:
    """ Copy entity data from a WCS workspace

    Copy entity data in an additive pattern from a source workspace
    to a target workspace. copy is additive with existing
    data and will not replace existing data

    parameters:
    entity: name of entity to copy
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
            'entity',
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
        entity_data_res = source_conv.get_entity(
            workspace_id=source_workspace,
            entity=entity,
            export=True
        )
    except WatsonException:
        raise ValueError("Unable to read source entity")

    entity_values = []
    entity_synonyms = []
    for value in entity_data_res['values']:
        # break out of anything except synonyms
        if value['type'] != 'synonyms':
            continue

        if not value['synonyms']:
            entity_values.append(value['value'])
            entity_synonyms.append('')

        for synonym in value['synonyms']:
            entity_values.append(value['value'])
            entity_synonyms.append(synonym)

    # generate the dataframe
    entity_data = pd.DataFrame(data={
        "action": ['ADD'] * len(entity_synonyms),
        "entity": [entity] * len(entity_synonyms),
        "value": entity_values,
        "synonym": entity_synonyms
    })
    config_data = {
        "clear_existing": clear_existing
    }

    # call the function
    _load_entity_data(conversation=target_conv,
                      workspace_id=target_workspace,
                      entity_data=entity_data,
                      config_data=config_data)

    print("copy_entity_data for '{}' complete.".format(entity))
