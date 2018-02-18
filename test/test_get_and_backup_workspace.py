""" Unit Testing get_and_backup_workspaces
"""
import json
from wcs_deployment_utils.util import get_and_backup_workspace
from watson_developer_cloud import ConversationV1
import responses
import pytest

from ._util import get_stored_json, build_workspace_from_json

live = pytest.mark.live #pylint: disable=c0103
mock = pytest.mark.mock #pylint: disable=c0103

TEST_USERNAME = 'test'
TEST_PASSWORD = 'test'
TEST_VERSION = '2017-05-26'
TEST_WORKSPACE = 'test'


@responses.activate
@mock
def test_mock_reponse(tmpdir):
    """ Tests against stubbed response
    """
    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_WORKSPACE, TEST_VERSION),
        json=get_stored_json('test/workspace_exports/test.json'),
        status=200)

    export_path = '{}/export.json'.format(tmpdir)

    res = get_and_backup_workspace(
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
        workspace=TEST_WORKSPACE,
        version=TEST_VERSION,
        export_path=export_path
    )
    export = None
    with open(export_path) as exp:
        export = json.load(exp)

    assert res['name'] == 'TEST'
    assert isinstance(res['intents'], list)
    assert isinstance(res['entities'], list)
    assert isinstance(res['dialog_nodes'], list)
    assert export == res

@live
def test_live_reponse(tmpdir):
    """ Tests against live response
    """
    export_path = '{}/export.json'.format(tmpdir)

    credentials = get_stored_json('test/config/test_credentials.json')

    conv = ConversationV1(
        username=credentials['username'],
        password=credentials['password'],
        version=credentials['version']
    )

    workspace_id = build_workspace_from_json(
        'test/workspace_exports/test.json',
        'test/config/test_credentials.json',
        'source_test'
    )

    res = get_and_backup_workspace(
        username=credentials['username'],
        password=credentials['password'],
        workspace=workspace_id,
        version=credentials['version'],
        export_path=export_path
    )
    export = None
    with open(export_path) as exp:
        export = json.load(exp)

    assert isinstance(res['name'], str)
    assert isinstance(res['intents'], list)
    assert isinstance(res['entities'], list)
    assert isinstance(res['dialog_nodes'], list)
    assert export == res

    conv.delete_workspace(workspace_id)
  