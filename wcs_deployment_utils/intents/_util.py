""" Module containing utility functions for intent operations
"""

import pandas as pd
from watson_developer_cloud import ConversationV1, WatsonException

def _load_intent_data(
        conversation: ConversationV1 = None,
        workspace_id: str = None,
        intent_data: pd.DataFrame = None,
        config_data: dict = None):
    """ Add all the intent data to the target workspace

    parameters:
    conversation: instance of Conversation from WDC SDK
    workspace_id: target workspace id
    intent_data: DataFrame of intent data with columns
        [action, intent, example]
    config_data: Dict of configuration options
        clear_existing: will clear existing examples from target
    """

    # optionally destroy any existing intents
    try:
        if config_data['clear_existing']:
            for intent_name in intent_data['intent'].unique():
                try:
                    conversation.delete_intent(workspace_id=workspace_id,
                                               intent=intent_name)
                    print("Intent '{}' removed".format(intent_name))
                except WatsonException:
                    print(("Intent '{}' does not exist"
                           ", nothing to remove").format(intent_name))
    except KeyError:
        print('Invalid config.json file')

    # handle removes
    rows_to_remove = intent_data[intent_data['action'] == 'REMOVE']
    for _, row in rows_to_remove.iterrows():
        try:
            # delete entire intent
            if row['intent'] != '' and row['example'] == '':
                try:
                    conversation.delete_intent(workspace_id=workspace_id,
                                               intent=row['intent'])
                    print("Intent '{}' removed".format(
                        row['intent']))
                except WatsonException:
                    try:
                        conversation.get_intent(workspace_id=workspace_id,
                                                intent=row['intent'])
                        # If no error is thrown, the intent failed to remove
                        print("Intent '{}' failed to remove".format(
                            row['intent']))
                    # if error is thrown, the example never existed so
                    # nothing else to do
                    except WatsonException:
                        print(("Intent '{}' does not "
                               "exist. Nothing to remove").format(
                                   row['intent']))

            # delete intent example
            if row['intent'] != '' and row['example'] != '':
                try:
                    conversation.delete_example(workspace_id=workspace_id,
                                                intent=row['intent'],
                                                text=row['example'])
                    print("Example '{}' removed for intent '{}'".format(
                        row['example'],
                        row['intent']))
                except WatsonException:
                    try:
                        conversation.get_example(workspace_id=workspace_id,
                                                 intent=row['intent'],
                                                 text=row['example'])
                        # If no error is thrown, the example failed to remove
                        print(("Intent '{}' failed to remove "
                               "example {}").format(
                                   row['example'],
                                   row['intent']))
                    # if error is thrown, the example never existed so
                    # nothing else to do
                    except WatsonException:
                        print(("Example '{}' does not "
                               "exist for intent '{}'. Nothing "
                               "to remove").format(
                                   row['example'],
                                   row['intent']))
        except KeyError:
            print('Intent data is not properly formed.')
            return

    # collect all intents and examples into a dictionary
    intents_to_add = {}
    rows_to_add = intent_data[intent_data['action'] == 'ADD']

    for intent_name in rows_to_add['intent'].unique():
        # load dictionary with empty lists
        intents_to_add[intent_name] = []

    # build intent data
    for _, row in rows_to_add.iterrows():
        # add the example to the to_add dictionary
        # skip empty entries
        if row['example'] == '':
            continue
        intents_to_add[row['intent']].append(row['example'])
    for intent_name, examples in intents_to_add.items():
        if intent_name != '' and not examples:
            print("No examples for intent '{}'".format(
                intent_name))
            continue
        try:
            # check if intent exists already
            _existing_intent_response = conversation.get_intent(
                workspace_id=workspace_id,
                intent=intent_name,
                export=True)
            intent_exists = True
            # build list of existing examples
            existing_examples = [example['text'] \
                for example in _existing_intent_response['examples']]
        # the intent does not already exist
        except WatsonException:
            intent_exists = False
            existing_examples = []
        # combine the existing examples with the new ones
        try:
            examples = list(set(existing_examples + examples))
            example_array = [{"text": x} for x in examples]
            # if the intent exists, we update, otherwise create
            if intent_exists:
                _existing_description = (
                    _existing_intent_response['description'])
                conversation.update_intent(workspace_id=workspace_id,
                                           intent=intent_name,
                                           new_examples=example_array)
                print("Intent '{}' updated. now contains {} examples".format(
                    intent_name,
                    len(examples)))
            else:
                conversation.create_intent(workspace_id=workspace_id,
                                           intent=intent_name,
                                           description=None,
                                           examples=example_array)
                print("Intent '{}' created with {} examples".format(
                    intent_name,
                    len(examples)))
        except WatsonException as err:
            print(repr(err))
            print("Intent '{}' failed to create".format(intent_name))
