""" Unit Testing copy_dialog_branch
"""
from wcs_deployment_utils.dialog import copy_dialog_branch
from wcs_deployment_utils.dialog._util import _get_matcher_function
from watson_developer_cloud import ConversationV1
import responses
import pytest
import anytree

from ._util import get_stored_json, build_workspace_from_json

live = pytest.mark.live #pylint: disable=c0103
mock = pytest.mark.mock #pylint: disable=c0103

TEST_USERNAME = 'test'
TEST_PASSWORD = 'test'
TEST_VERSION = '2017-05-26'
TEST_TARGET_WORKSPACE = 'target'
TEST_SOURCE_WORKSPACE = 'source'

CASES = get_stored_json('test/parameters/copy_dialog_branch_params.json')

def _test_id_name(case: dict):
    return case['name']

@responses.activate
@mock
@pytest.mark.parametrize('params', CASES, ids=_test_id_name)
def test_mock_response(params, tmpdir):
    """ Tests against stubbed response
    """
    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_TARGET_WORKSPACE, TEST_VERSION),
        json=get_stored_json('test/workspace_exports/test.json'),
        status=200)

    responses.add(
        responses.GET,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_SOURCE_WORKSPACE, TEST_VERSION),
        json=get_stored_json('test/workspace_exports/order_pizza.json'),
        status=200)

    responses.add(
        responses.POST,
        'https://gateway.watsonplatform.net/conversation/api/v1/workspaces/{}?version={}'
        .format(TEST_TARGET_WORKSPACE, TEST_VERSION),
        json={},
        status=200)

    export_path = '{}/export.json'.format(tmpdir)

    tree, rep = copy_dialog_branch(
        root_node='order a pizza',
        target_node=params['target_node'],
        target_insert_as=params['target_insert_as'],
        source_username=TEST_USERNAME,
        source_password=TEST_PASSWORD,
        source_workspace=TEST_SOURCE_WORKSPACE,
        target_username=TEST_USERNAME,
        target_password=TEST_PASSWORD,
        target_workspace=TEST_TARGET_WORKSPACE,
        version=TEST_VERSION,
        target_backup_file=export_path)

    # expected parent id from params
    expected_parent_id = _get_id_at(
        params['expected_parent'],
        tree)

    # expected previous sibling id from params
    expected_previous_sibling_id = _get_id_at(
        params['expected_previous_sibling'],
        tree)

    # expected displaced node from params
    displaced_node = _get_node_at(
        params['displaced'],
        tree)

    # expected jt parent id from params
    jt_expected_parent_id = _get_id_at(
        params['jump_to_expected_parent'],
        tree)

    # expected jt previous sibling id from params
    jt_expected_previous_sibling_id = _get_id_at(
        params['jump_to_expected_previous_sibling'],
        tree)

    # expected jumpt to displaced node from params
    jt_displaced_node = _get_node_at(
        params['displaced_jump_to'],
        tree)

    main_insert_matches = anytree.search.findall(
        tree,
        filter_=_get_matcher_function('order a pizza', id_only=False))

    # check that there's a single source branch insert
    assert len(main_insert_matches) == 1

    insert_branch = main_insert_matches[0]

    # check that it's inserted  in expected location
    assert insert_branch.node['parent'] == expected_parent_id
    assert insert_branch.node['previous_sibling'] == expected_previous_sibling_id

    #check that displaced node (if any) has been moved
    if (displaced_node is not None and
            displaced_node.id is not None):
        assert displaced_node.node['previous_sibling'] == insert_branch.id

    # check that all nodes are included
    assert len(insert_branch.descendants) == 22

    # check that the jump has been included
    jump_insert_matches = anytree.search.findall(
        tree,
        filter_=_get_matcher_function('get name', id_only=False))

    # check that there's a single source branch insert
    assert len(jump_insert_matches) == 1

    jump_insert_node = jump_insert_matches[0]
    # check that it's inserted as last child

    # check that it's inserted as last valid child of root
    assert jump_insert_node.node['parent'] is jt_expected_parent_id
    assert jump_insert_node.node['previous_sibling'] is jt_expected_previous_sibling_id

    # check that the displaced nodes (if any) were moved
    if (jt_displaced_node is not None and
            jt_displaced_node.id is not None):
        assert jt_displaced_node.node['previous_sibling'] == jump_insert_node.id

    # check that the correct number of nodes are included
    assert len(tree.descendants) == 38

    # check that a representation is returned
    assert isinstance(rep, str)

# TODO add teardown for failed cases
@live
def test_live_response(tmpdir):
    """ Create a test and source workspace, test a dialog branch copy, then
    destroy the created workspaces
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

    tree, _ = copy_dialog_branch(
        root_node='order a pizza',
        target_node='root',
        target_insert_as='child',
        source_username=target_credentials['username'],
        source_password=target_credentials['password'],
        source_workspace=source_workspace,
        target_username=target_credentials['username'],
        target_password=target_credentials['password'],
        target_workspace=target_workspace,
        version=target_credentials['version'],
        target_backup_file=export_path)

    # basic assert that results are as expected
    assert len(tree.descendants) == 38

    # primary test is that no exception is raised

    # clean up
    target.delete_workspace(target_workspace)
    target.delete_workspace(source_workspace)

def _get_node_at(identifier: str, tree_root: anytree.AnyNode) -> anytree.AnyNode:
    matches = anytree.search.findall(
        tree_root,
        filter_=_get_matcher_function(
            identifier,
            id_only=False))
    if len(matches) > 1:
        raise RuntimeError('identifier: {} matched multiple nodes'.format(identifier))
    elif not matches:
        raise RuntimeError('identifier: {} did not match a node'.format(identifier))
    else:
        return matches[0]

def _get_id_at(identifier: str, tree_root: anytree.AnyNode) -> anytree.AnyNode:
    matches = anytree.search.findall(
        tree_root,
        filter_=_get_matcher_function(
            identifier,
            id_only=False))
    if len(matches) > 1:
        raise RuntimeError('identifier: {} matched multiple nodes'.format(identifier))
    elif not matches:
        raise RuntimeError('identifier: {} did not match a node'.format(identifier))
    else:
        return matches[0].id
