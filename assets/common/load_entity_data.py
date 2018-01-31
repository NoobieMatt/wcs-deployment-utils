import pandas as pd
import numpy as np
import json
from watson_developer_cloud import ConversationV1, WatsonException

# Right now this doesn't support patterns. This should be 
# updated when the APIs for managing patterns are made available
# Alternatively, this can be updated with the values API to move
# beyond this limitation or an alternative function could be developed
# to specifically handle patterns


def load_csv_as_entity_data(conversation_username=None, 
                            conversation_password=None, 
                            version=None,
                            workspace_id=None, 
                            action=None,
                            root_dir=None):

    """ Load entity data from a CSV file

    Currently can only handle synonym values 

    CSV file will be of the following structure:
    action,entity,value,synonym

    valid actions are "ADD" or "REMOVE"

    CSV file is located at: 
    {rootdir}/actions/load_entity_data/{action}/entities.csv

    remove statments will be executed first, then adds will be grouped
    and executed as a single statement. adds are additive with existing
    data and will not replace

    parameters:
    conversation_username: username for WCS instance
    conversation_password: password for WCS instance
    version: version of WCS API
    workspace_id: workspace_id for WCS instance
    action: directory containing entities.csv
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
    entity_data = pd.read_csv(
        '{}/actions/load_entity_data/{}/entities.csv'.format(
            root_dir, 
            action),
        dtype='str',
        keep_default_na=False
        )
    config_data = {}
    with open('{}/actions/load_entity_data/{}/config.json'.format(
            root_dir, action)) as config_file:
        config_data = json.load(config_file)

    # call the function
    _load_entity_data(conversation=conversation,
                      workspace_id=workspace_id,
                      entity_data=entity_data,
                      config_data=config_data)
    print(("load_csv_as_entity_data "
           "action '{}' complete.").format(action))    

    
def copy_entity_data(entity=None,
                     source_username=None,
                     source_password=None,
                     source_workspace=None,
                     target_username=None,
                     target_password=None,
                     target_workspace=None,
                     version=None,
                     clear_existing=False):
    """ Copy entity data from a WCS workspace

    Copy entity data in an additive pattern from a source workspace
    to a target workspace. copy is additive with existing
    data and will not replace existing data

    parameters:
    entity: name of entity to copy
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
        entity_data_res = source_conv.get_entity(
            workspace_id=source_workspace,
            entity=entity,
            export=True
        )
    except WatsonException as e:
        print("Unable to read source intent")
        return
    entity_values = []
    entity_synonyms = []
    for value in entity_data_res['values']:
        # break out of anything except synonyms
        if value['type'] != 'synonyms':
            continue
        
        if len(value['synonyms']) == 0:
            entity_values.append(value['value'])
            entity_synonyms.append('')
          
        for synonym in value['synonyms']:
          entity_values.append(value['value'])
          entity_synonyms.append(synonym)

    # generate the dataframe
    entity_data = pd.DataFrame(data={
        "action": ['ADD'] * len(entity_synonyms),
        "entity": [entity] * len(entity_synonyms),
        "value": entity_values,
        "synonym": entity_synonyms
    })
    config_data = {
      "clear_existing": clear_existing
    }

    # call the function
    _load_entity_data(conversation=target_conv,
                      workspace_id=target_workspace,
                      entity_data=entity_data,
                      config_data=config_data)

    print("copy_entity_data for '{}' complete.".format(entity))


def _load_entity_data(conversation=None,
                      workspace_id=None,
                      entity_data=None,
                      config_data=None):
    
    """ Add all the entity data to the target workspace

    parameters:
    conversation: instance of Conversation from WDC SDK
    workspace_id: target workspace id
    intent_data: DataFrame of intent data with columns
        [action, entity, value, synonym]
    config_data: Dict of configuration options
        clear_existing: will clear existing examples from target
    """

    # validate that values are provided
    args = locals()
    for key in args:
        if args[key] is None:
            raise ValueError("Argument '{}' requires a value".format(key))
    
    # optionally destroy any existing entities
    try:
        if config_data['clear_existing']:
            for entity_name in entity_data['entity'].unique():
                try:
                    conversation.delete_entity(workspace_id=workspace_id,
                                               entity=entity_name)
                    print("entity '{}' removed".format(entity_name))
                except WatsonException as e:
                    print(("entity '{}' does not exist"
                          ", nothing to remove").format(entity_name))
    except KeyError as e:
        print('Invalid config.json file')


    # remove all the requested deletions first
    rows_to_remove = entity_data[entity_data['action'] == 'REMOVE']
    for _, row in rows_to_remove.iterrows():
        try:
            deletion_type = None
            # remove entire entity
            if (row['entity'] != '' and row['value'] == '' and
                    row['synonym'] == ''):
                deletion_type = 'ENT'
            # remove entire value
            elif (row['entity'] != '' and row['value'] != '' and
                    row['synonym'] == ''):
                deletion_type = 'VAL'
            # remove single synonym
            elif (row['entity'] != '' and row['value'] != '' and
                    row['synonym'] != ''):
                deletion_type = 'SYN'
            else:
                raise ValueError('Invalid REMOVE in entity data')

            # process each type of deletion
            
            # entity deletion
            if deletion_type == 'ENT':
                try:
                    # try to delete entity first
                    conversation.delete_entity(workspace_id=workspace_id, 
                                                entity=row['entity'])
                    print("Entity '{}' removed.".format(
                        row['entity']))
                except WatsonException as e:
                    try:
                        # if delete failed, check if it exists
                        conversation.get_entity(workspace_id=workspace_id, 
                                                entity=row['entity'])
                        print("Entity '{}' failed to remove.".format(
                            row['entity']))
                    except:
                        # if it doesn't exist, then there was nothing to
                        # delete
                        print(("Entity '{}' does not exist. "
                              "Nothing to remove").format(
                                  row['entity']))

            # value deletion
            if deletion_type == 'VAL':
                try:
                    # try to delete value first
                    conversation.delete_value(workspace_id=workspace_id, 
                                              entity=row['entity'],
                                              value=row['value'])
                    print("Value '{}' removed for entity '{}".format(
                        row['value'],
                        row['entity']))
                except WatsonException as e:
                    try:
                        # if delete failed, check if it exists
                        conversation.get_value(workspace_id=workspace_id, 
                                               entity=row['entity'],
                                               value=row['value'])
                        print(("Value '{}' failed to "
                               "remove for entity '{}'").format(
                                  row['value'],
                                  row['entity']))
                    except:
                        # if it doesn't exist, then there was nothing to
                        # delete
                        print(("Value '{}' does not exist "
                               "for entity '{}'. Nothing to "
                               "remove").format(
                                  row['value'],
                                  row['entity']))

            # synonym deletion
            if deletion_type == 'SYN':
                try:
                    # try to delete synonym first
                    conversation.delete_synonym(workspace_id=workspace_id,
                                                entity=row['entity'],
                                                value=row['value'],
                                                synonym=row['synonym'])
                    print(("Synonym '{}' from value '{}' removed "
                           "for entity '{}").format(
                              row['synonym'],
                              row['value'],
                              row['entity']))
                except WatsonException as e:
                    try:
                        # if delete failed, check if it exists
                        conversation.get_synonym(workspace_id=workspace_id, 
                                                 entity=row['entity'],
                                                 value=row['value'],
                                                 synonym=row['synonym'])
                        print(("Synonym '{}' for value '{}' failed to "
                               "remove for entity '{}'").format(
                                  row['synonym'],
                                  row['value'],
                                  row['entity']))
                    except:
                        # if it doesn't exist, then there was nothing to
                        # delete
                        print(("Synyonym '{}' for value '{}' does not exist "
                               "for entity '{}'. Nothing to "
                               "remove").format(
                                  row['synonym'],
                                  row['value'],
                                  row['entity']))
        except ValueError as e:
            print(repr(e))
        except KeyError as e:
            print('entity data is not properly formed')
        
    # process the additions
    # collect all intents and examples into a dictionary
    entities_to_add = []
    rows_to_add = entity_data[entity_data['action'] == 'ADD']
    entities_to_add = list(rows_to_add['entity'].unique())

    # iterate through entities
    for entity_name in entities_to_add:
      
        new_values = []
        # rows containing data on the current entity
        entity_rows = rows_to_add[rows_to_add['entity'] == entity_name]

        # unique values for that entity
        values_to_add = list(entity_rows['value'].unique())

        for value in values_to_add:
            if value == '':
                continue
            # rows for current entity and value
            value_rows = entity_rows[entity_rows['value'] == value]
            # unique synonyms for current entity and value
            synonyms = list(value_rows['synonym'].unique())

            # remove empty strings
            synonyms = [synonym for synonym in synonyms if synonym != '']

            value = {
              "value": value
            }

            if (len(synonyms) > 0):
                value['synonyms'] = synonyms

            new_values.append(value)

        try:
            # check if there is an existing entity
            existing_entity = conversation.get_entity(
                workspace_id=workspace_id,
                entity=entity_name,
                export=True)
        except WatsonException as e:
            existing_entity = None
        
        # if there is no existing entity, we can just create it now
        # with the information that we have
        if existing_entity is None:
            try:
                conversation.create_entity(
                    workspace_id=workspace_id,
                    entity=entity_name,
                    values=new_values)
                print(("Entity '{}' update complete for all "
                       "values and synyonyms").format(entity_name))
            except WatsonException as e:
                print(repr(e))
                print(("Entity '{}' creation failed for all "
                       "values and synyonyms").format(entity_name))
        # now things get tricky. we need to combine entity values
        else:
            new_values_names = [value['value'] for value in new_values]
            existing_values_names = [value['value'] \
                for value in existing_entity['values']]
            
            # dictionaries to make life easier
            new_value_dict = {}
            existing_value_dict = {}

            for value in new_values:
                value_name = value['value']
                new_value_dict[value_name] = value

            for value in existing_entity['values']:
                value_name = value['value']
                existing_value_dict[value_name] = value
            
            # leave existing, add new ones, and merge intersection
            value_names_to_append = list(set(new_values_names) - \
                set(existing_values_names))
            values_to_merge = list(set(new_values_names) & \
                set(existing_values_names))
            value_names_to_retain = list(set(existing_values_names) - \
                set(new_values_names))

            # we'll store the updated value list here
            # list is retained + new + merged
            final_values = []

            # add in the retained
            for value_name in value_names_to_retain:
                final_values.append(existing_value_dict[value_name])

            # add in the new
            for value_name in value_names_to_append:
                final_values.append(new_value_dict[value_name])

            # merge the values that need to be merged
            # then add them to the list
            for value_name in values_to_merge:
                existing_value = existing_value_dict[value_name]
                new_value = new_value_dict[value_name]
                # confirm that we're working with synonyms
                if existing_value['type'] != 'synonyms':
                    print(("Value type mismatch for value '{}' "
                           " in entity '{}'. Cannot process value.").format(
                             value_name,
                             entity_name))
                    continue
                # get a list of the synonyms
                # existing synonyms (may be empty set)
                try:
                  existing_synoyms = existing_value['synonyms']
                except:
                  existing_synoyms = []

                # new synonyms (may be empty set)
                try:
                    new_synonyms = new_value['synonyms']
                except:
                    new_synonyms = []
                # merge the set
                merged_synonyms = list(set(existing_synoyms + new_synonyms))

                # add the new value to the master list
                merged_value = existing_value
                merged_value['synonyms'] = merged_synonyms
                final_values.append(merged_value)
            
            # finally update the original entity
            try:
                conversation.update_entity(
                    workspace_id=workspace_id,
                    entity=entity_name,
                    new_values=final_values)
                print(("Entity '{}' update complete for all "
                       "values and synyonyms").format(entity_name))
            except WatsonException as e:
                print(final_values)
                print(repr(e))
                print(("Entity '{}' update failed for all "
                       "values and synyonyms").format(entity_name))