""" Unit Testing load_intent_data_from_csv
"""
import json
from wcs_deployment_utils.intents import load_csv_as_intent_data
from watson_developer_cloud import ConversationV1
import pytest

from ._util import build_workspace_from_json, get_stored_json

live = pytest.mark.live #pylint: disable=c0103
mock = pytest.mark.mock #pylint: disable=c0103

@live
def test_live_response(tmpdir):
    """ Tests against stubbed response
    """

    target_credentials = get_stored_json('test/config/test_credentials.json')

    target = ConversationV1(
        username=target_credentials['username'],
        password=target_credentials['password'],
        version=target_credentials['version']
    )

    target_workspace = build_workspace_from_json(
        'test/workspace_exports/test.json',
        'test/config/test_credentials.json',
        'target_test'
    )

    export_path = '{}/export.json'.format(tmpdir)

    load_csv_as_intent_data(
        conversation_username=target_credentials['username'],
        conversation_password=target_credentials['password'],
        version=target_credentials['version'],
        workspace=target_workspace,
        csv_file='test/parameters/load_csv_as_intent_data.csv',
        clear_existing=False,
        target_backup_file=export_path)

    # verify backup was created
    export = None
    with open(export_path) as exp:
        export = json.load(exp)
    assert export is not None

    intent_1 = target.get_intent(target_workspace, '1', export=True)

    # assert that we have appended the new value
    assert intent_1 is not None
    assert 'TEST_1_APPEND' in [x['text'] for x in intent_1['examples']]

    with pytest.raises(Exception):
        target.get_intent(target_workspace, '2', export=True)
    
    intent_3 = target.get_intent(target_workspace, '3', export=True)
    # assert that we have appended the new value
    assert intent_3 is not None
    assert 'TEST3' in [x['text'] for x in intent_3['examples']]

    # clean up
    target.delete_workspace(target_workspace)
