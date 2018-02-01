import sys
sys.path.append('./common')
sys.path.append('.')

from _credentials import (CONVERSATION_USERNAME, 
                          CONVERSATION_PASSWORD, 
                          VERSION, 
                          TARGET_WORKSPACE, 
                          WORKSPACE_ID)

from load_intent_data import load_csv_as_intent_data
from load_entity_data import load_csv_as_entity_data

load_csv_as_intent_data(conversation_username=CONVERSATION_USERNAME,
                        conversation_password=CONVERSATION_PASSWORD,
                        version=VERSION,
                        workspace_id=TARGET_WORKSPACE,
                        action='test',
                        root_dir='.')

load_csv_as_entity_data(conversation_username=CONVERSATION_USERNAME,
                        conversation_password=CONVERSATION_PASSWORD,
                        version=VERSION,
                        workspace_id=TARGET_WORKSPACE,
                        action='test',
                        root_dir='.')