""" Unit Testing load_entity_data_from_csv
"""
import json
from wcs_deployment_utils.entities import load_csv_as_entity_data
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

    load_csv_as_entity_data(
        conversation_username=target_credentials['username'],
        conversation_password=target_credentials['password'],
        version=target_credentials['version'],
        workspace=target_workspace,
        csv_file='test/parameters/load_csv_as_entity_data.csv',
        clear_existing=False,
        target_backup_file=export_path)

    # verify backup was created
    export = None
    with open(export_path) as exp:
        export = json.load(exp)
    assert export is not None

    target.get_synonym(target_workspace, 'TEST_1', '1', 'TEST_ONE_APPEND')
    target.get_synonym(target_workspace, 'TEST_1', '3', 'TEST')
    target.get_value(target_workspace, 'TEST_3', 'TEST', export=False)
    target.get_entity(target_workspace, 'TEST_2', export=False)

    with pytest.raises(Exception):
        target.get_value(target_workspace, 'TEST_1', '2', export=False)

    # clean up
    target.delete_workspace(target_workspace)
