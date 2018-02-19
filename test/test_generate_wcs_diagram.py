""" Unit Testing get_and_backup_workspaces
"""
import json
from wcs_deployment_utils.dialog import generate_wcs_diagram
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
def test_mock_reponse():
    """ Tests against stubbed response
    """
    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_WORKSPACE, TEST_VERSION),
        json=get_stored_json('test/workspace_exports/test.json'),
        status=200)

    projection = generate_wcs_diagram(
        conversation_username=TEST_USERNAME,
        conversation_password=TEST_PASSWORD,
        workspace=TEST_WORKSPACE,
        version=TEST_VERSION)

    assert len(projection.splitlines()) == 11

@live
def test_live_reponse():
    """ Tests against live response
    """
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

    projection = generate_wcs_diagram(
        conversation_username=credentials['username'],
        conversation_password=credentials['password'],
        workspace=workspace_id,
        version=credentials['version'])

    assert len(projection.splitlines()) == 11

    conv.delete_workspace(workspace_id)
  