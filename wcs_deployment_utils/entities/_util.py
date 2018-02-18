""" Module containing utility functions for entity operations
"""

import pandas as pd
from watson_developer_cloud import ConversationV1, WatsonException

# Right now this doesn't support patterns. This should be
# updated when the APIs for managing patterns are made available
# Alternatively, this can be updated with the values API to move
# beyond this limitation or an alternative function could be developed
# to specifically handle patterns

def _load_entity_data(conversation: ConversationV1 = None,
                      workspace_id: str = None,
                      entity_data: pd.DataFrame = None,
                      config_data: dict = None):
    
    """ Add all the entity data to the target workspace

    parameters:
    conversation: instance of Conversation from WDC SDK
    workspace_id: target workspace id
    entity_data: DataFrame of intent data with columns
        [action, entity, value, synonym]
    config_data: Dict of configuration options
        clear_existing: will clear existing examples from target
    """
    
    # optionally destroy any existing entities
    try:
        if config_data['clear_existing']:
            for entity_name in entity_data['entity'].unique():
                try:
                    conversation.delete_entity(workspace_id=workspace_id,
                                               entity=entity_name)
                    print("entity '{}' removed".format(entity_name))
                except WatsonException:
                    print(("entity '{}' does not exist"
                           ", nothing to remove").format(entity_name))
    except KeyError:
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
                except WatsonException:
                    try:
                        # if delete failed, check if it exists
                        conversation.get_entity(workspace_id=workspace_id,
                                                entity=row['entity'])
                        print("Entity '{}' failed to remove.".format(
                            row['entity']))
                    except WatsonException:
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
                except WatsonException:
                    try:
                        # if delete failed, check if it exists
                        conversation.get_value(workspace_id=workspace_id,
                                               entity=row['entity'],
                                               value=row['value'])
                        print(("Value '{}' failed to "
                               "remove for entity '{}'").format(
                                   row['value'],
                                   row['entity']))
                    except WatsonException:
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
                except WatsonException:
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
                    except WatsonException:
                        # if it doesn't exist, then there was nothing to
                        # delete
                        print(("Synyonym '{}' for value '{}' does not exist "
                               "for entity '{}'. Nothing to "
                               "remove").format(
                                   row['synonym'],
                                   row['value'],
                                   row['entity']))
        except ValueError as err:
            print(repr(err))
        except KeyError:
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

            if synonyms:
                value['synonyms'] = synonyms

            new_values.append(value)

        try:
            # check if there is an existing entity
            existing_entity = conversation.get_entity(
                workspace_id=workspace_id,
                entity=entity_name,
                export=True)
        except WatsonException:
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
            except WatsonException as err:
                print(repr(err))
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
                except KeyError:
                    existing_synoyms = []

                # new synonyms (may be empty set)
                try:
                    new_synonyms = new_value['synonyms']
                except KeyError:
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
            except WatsonException as err:
                print(final_values)
                print(repr(err))
                print(("Entity '{}' update failed for all "
                       "values and synyonyms").format(entity_name))
