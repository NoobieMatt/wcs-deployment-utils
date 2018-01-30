import pandas as pd
import numpy as np
import json
from watson_developer_cloud import ConversationV1, WatsonException

def load_csv_as_intent_data(conversation_username=None,
                            conversation_password=None,
                            version=None, 
                            workspace_id=None, 
                            action=None,
                            root_dir=None):
    """ Load intent data from a CSV file

    CSV file will be of the following structure:
    action,intent,example

    valid actions are "ADD" or "REMOVE"

    CSV file is located at: {rootdir}/actions/{action}/examples.csv

    remove statments will be executed first, then adds will be grouped
    and executed as a single statement. adds are additive with existing
    data and will not replace

    parameters:
    conversation_username: username for WCS instance
    conversation_password: password for WCS instance
    version: version of WCS API
    workspace_id: workspace_id for WCS instance
    action: directory containing examples.csv
    root_dir: root directory containing actions directory
    """
    # validate that values are provided
    args = locals()
    for key in args:
        if args[key] is None:
            raise ValueError("Argument '{}' requires a value".format(key))
    
    # setup conversation class
    conversation = ConversationV1(
        username=conversation_username,
        password=conversation_password,
        version= version
    )
    
    # load data
    intent_data = pd.read_csv(
        '{}/actions/load_intent_data/{}/examples.csv'.format(
            root_dir,
            action),
        dtype='str',
        keep_default_na=False)
    config_data = {}
    with open('{}/actions/load_intent_data/{}/config.json'.format(
            root_dir, action)) as config_file:    
        config_data = json.load(config_file)
    
    # call the function
    _load_intent_data(conversation=conversation,
                      workspace_id=workspace_id,
                      intent_data=intent_data,
                      config_data=config_data)
    print("load_intent_data action '{}' complete.".format(action))


def copy_intent_data(intent=None,
                     source_username=None,
                     source_password=None,
                     source_workspace=None,
                     target_username=None,
                     target_password=None,
                     target_workspace=None,
                     version=None,
                     clear_existing=False):
    """ Copy intent data from a WCS workspace

    Copy intent data in an additive pattern from a source workspace
    to a target workspace. copy is additive with existing
    data and will not replace existing data

    parameters:
    intent: name of intent to copy
    source_username: username for source WCS instance
    source_password: password for source WCS instance
    source_workspace: workspace id for source WCS instance
    target_username: username for target WCS instance
    target_password: password for target WCS instance
    target_workspace: workspace id for target WCS instance
    version: version of WCS instances
    clear_existing: boolean to clear existing intent data from target
    """

    # validate that values are provided
    args = locals()
    for key in args:
        if args[key] is None:
            raise ValueError("Argument '{}' requires a value".format(key))
    
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
        intent_data_res = source_conv.get_intent(
            workspace_id=source_workspace,
            intent=intent,
            export=True
        )
    except WatsonException as e:
        print("Unable to read source intent")
        return
    intent_examples = []
    for example in intent_data_res['examples']:
        intent_examples.append(example['text'])
    
    intent_data = pd.DataFrame(data={
        "action": ['ADD'] * len(intent_examples),
        "intent": [intent] * len(intent_examples),
        "example": intent_examples
    })
    config_data = {
      "clear_existing": clear_existing
    }

    # call the function
    _load_intent_data(conversation=target_conv,
                      workspace_id=target_workspace,
                      intent_data=intent_data,
                      config_data=config_data)

    print("copy_intent_data for '{}' complete.".format(intent))



def _load_intent_data(conversation=None, workspace_id=None, intent_data=None,
                     config_data=None):
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
                except WatsonException as e:
                    print(("Intent '{}' does not exist",
                           ", nothing to remove").format(intent_name))
    except KeyError as e:
        print('Invalid config.json file')

    # handle removes
    rows_to_remove = intent_data[intent_data['action'] == 'REMOVE']
    for _ , row in rows_to_remove.iterrows():
        try:
          # delete entire intent
          if row['intent'] != '' and row['example'] == '':
              try:
                  conversation.delete_intent(workspace_id=workspace_id, 
                                              intent=row['intent'])
                  print("Intent '{}' removed".format(
                      row['intent']))
              except WatsonException as e:
                  try:
                      conversation.get_intent(workspace_id=workspace_id, 
                                               intent=row['intent'])
                      # If no error is thrown, the intent failed to remove
                      print("Intent '{}' failed to remove".format(
                          row['intent']))
                  # if error is thrown, the example never existed so
                  # nothing else to do
                  except:
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
              except WatsonException as e:
                  try:
                      conversation.get_example(workspace_id=workspace_id, 
                                               intent=row['intent'],
                                               text=row['example'])
                      # If no error is thrown, the example failed to remove
                      print("Intent '{}' failed to remove".format(
                          row['example'],
                          row['intent']))
                  # if error is thrown, the example never existed so
                  # nothing else to do
                  except:
                      print(("Example '{}' does not "
                             "exist for intent '{}'. Nothing "
                             "to remove").format(
                                row['example'],
                                row['intent']))
        except KeyError as e:
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
        if intent_name != '' and len(examples) == 0:
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
        except WatsonException as e:
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
        except WatsonException as e:
            print(repr(e))
            print("Intent '{}' failed to create".format(
                      intent_name,
                      len(examples)))