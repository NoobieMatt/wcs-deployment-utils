""" Unit Testing copy_entity_data
"""
import json
from wcs_deployment_utils.entities import copy_entity_data
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

    source_workspace = build_workspace_from_json(
        'test/workspace_exports/order_pizza.json',
        'test/config/test_credentials.json',
        'source_test'
    )

    target_workspace = build_workspace_from_json(
        'test/workspace_exports/test.json',
        'test/config/test_credentials.json',
        'target_test'
    )

    export_path = '{}/export.json'.format(tmpdir)

    copy_entity_data(
        entity='pizza_topping',
        source_username=target_credentials['username'],
        source_password=target_credentials['password'],
        source_workspace=source_workspace,
        target_username=target_credentials['username'],
        target_password=target_credentials['password'],
        target_workspace=target_workspace,
        version=target_credentials['version'],
        clear_existing=False,
        target_backup_file=export_path)

    # verify backup was created
    export = None
    with open(export_path) as exp:
        export = json.load(exp)
    assert export is not None

    intent = target.get_entity(target_workspace, 'pizza_topping', export=False)
    assert intent is not None

    # clean up
    target.delete_workspace(target_workspace)
    target.delete_workspace(source_workspace)
