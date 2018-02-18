""" Testing utilities
"""
import json
from watson_developer_cloud import ConversationV1

def get_stored_json(filename: str) -> dict:
    """ returns a local copy of a WCS export
    """
    response = None
    with open(filename, 'r', encoding='utf8') as exp:
        response = json.load(exp)
    if response is None:
        raise RuntimeError('Unable to load export {}'.format(filename))
    return response

def build_workspace_from_json(
        json_filename: str,
        credentials_filename: str,
        name: str) -> str:
    """ returns a workspace id of a workspace created from json file
    uses credentials stored in json file at `credentials_filename`.
    expects to find `username`, `password`, and `version`
    """
    target_credentials = get_stored_json(credentials_filename)

    target = ConversationV1(
        username=target_credentials['username'],
        password=target_credentials['password'],
        version=target_credentials['version']
    )

    export = get_stored_json(json_filename)

    t_res = target.create_workspace(
        name=name,
        intents=export['intents'],
        entities=export['entities'],
        dialog_nodes=export['dialog_nodes'])

    return t_res['workspace_id']
