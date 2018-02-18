""" Unit Testing delete_branch_from_csv module
"""
import json
from wcs_deployment_utils.dialog import delete_branch_from_csv
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
    # test against test workspace
    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_WORKSPACE, TEST_VERSION),
        json=get_stored_json('test/workspace_exports/test.json'),
        status=200)

    node_2_1 = 'node_4_1518675295323'
    node_2 = 'node_2_1518675282908'
    does_not_exist = 'DOESNOTEXIST'

    # node 2 reports that it can be deleted successfully
    responses.add(
        responses.DELETE,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}/dialog_nodes/{}?version={}'
        .format(TEST_WORKSPACE, node_2, TEST_VERSION),
        json={},
        status=200)

    # node 2_1 reports that it cannot be deleted successfully
    responses.add(
        responses.DELETE,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}/dialog_nodes/{}?version={}'
        .format(TEST_WORKSPACE, node_2_1, TEST_VERSION),
        json={},
        status=400)

    # node 2_1 reports that it does not exist
    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}/dialog_nodes/{}?version={}'
        .format(TEST_WORKSPACE, node_2_1, TEST_VERSION),
        json={},
        status=400)

    export_path = '{}/export.json'.format(tmpdir)

    deleted, not_found = delete_branch_from_csv(
        conversation_username=TEST_USERNAME,
        conversation_password=TEST_PASSWORD,
        workspace=TEST_WORKSPACE,
        version=TEST_VERSION,
        csv_file='test/parameters/delete_branch_from_csv.csv',
        target_backup_file=export_path)

    # verify backup was created
    export = None
    with open(export_path) as exp:
        export = json.load(exp)
    assert export is not None

    # should have deleted node 2
    assert node_2 in [x[1] for x in deleted]
    # node 2_1 was deleted as part of delete of node 2
    # but not directly deleted
    assert node_2_1 in [x[1] for x in deleted]
    # no action to take on DOESNOTEXIST since it is not found in target
    assert does_not_exist in not_found

@live
def test_live_reponse(tmpdir):
    """ Tests against stubbed response
    """
    export_path = '{}/export.json'.format(tmpdir)

    credentials = get_stored_json('test/config/test_credentials.json')

    node_2_1 = 'node_4_1518675295323'
    node_2 = 'node_2_1518675282908'
    does_not_exist = 'DOESNOTEXIST'

    conv = ConversationV1(
        username=credentials['username'],
        password=credentials['password'],
        version=credentials['version']
    )

    workspace_id = build_workspace_from_json(
        'test/workspace_exports/test.json',
        'test/config/test_credentials.json',
        'target_test'
    )

    deleted, not_found = delete_branch_from_csv(
        conversation_username=credentials['username'],
        conversation_password=credentials['password'],
        workspace=workspace_id,
        version=credentials['version'],
        csv_file='test/parameters/delete_branch_from_csv.csv',
        target_backup_file=export_path)
    
    # verify backup was created
    export = None
    with open(export_path) as exp:
        export = json.load(exp)
    assert export is not None

    # should have deleted node 2
    assert node_2 in [x[1] for x in deleted]
    # node 2_1 was deleted as part of delete of node 2
    # but not directly deleted
    assert node_2_1 in [x[1] for x in deleted]
    # no action to take on DOESNOTEXIST since it is not found in target
    assert does_not_exist in not_found

    conv.delete_workspace(workspace_id)
  