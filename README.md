# Watson Conversation Deployment Utilities

A set of utilities to script common Watson Conversation tasks without using the service tooling.

These are particularly useful if you need to build or apply changes to a set of Watson Conversation instances in an additive, programmatic, and repeatable way. A few examples of useful situations for these utilities:

1. You want to copy a dialog branch from one workspace to another without overwriting the entire dialog tree
2. You want to merge entity definitions from one workspace to another without overwriting existing entity components
3. You want to build a workspace as a set of modular components. (Workspace 1 uses modules A and C, but workspace 2 uses modules B and C)

## Get Started

To install:

`pip install watson-deployment-utils`

Then import the library into your python project and use

## Included Functions

### copy\_dialog\_data

Module: `wcs_deployment_utils.dialog.copy_dialog_data`

Copy a branch of dialog from a source workspace to a target workspace.

Default insert is 'sibling' which inserts the branch as the immediate sibling of the target node. Alternatively, 'child' or 'last_child' can be specified so that the branch is inserted as the first or last child of the node. If `target_node` is specified as 'root', the branch can be inserted as the first child of the dialog root

Any existing nodes with the same name or ID will be deleted.

These options are summarized below

```
    Root
    |
    |--Target Node
    |       |
    |       |<-(insert as child)
    |       |
    |       |--Existing Node
    |       |
    |       |<-(insert as last_child)
    |       |
    |       |--"true" node
    |
    |<-(insert as sibling)
    |
    ...
```
**parameters**:

`root_node`: ID or title of the root node in source

`target_node`: ID or title of the root node in target

`target_insert_as`: Default 'child'. Location of branch insertion, with respect to the target node. valid options ['child', 'last_child' or 'sibling']

`source_username`: Username for source WCS instance

`source_password`: Password for source WCS instance

`source_workspace`: Workspace ID for source WCS instance

`target_username`: Username for target WCS instance

`target_password`: Password for target WCS instance

`target_workspace`: Workspace ID for target WCS instance

`version`: WCS API version

`target_backup_file`: write a backup of target workspace to this file

**returns**:

`target_nodes`: the root node of the projected target tree

`projected`: a string representation of the projected tree


**Example**:

```
from wcs_deployment_utils.dialog import copy_dialog_data

_, projection = copy_dialog_branch(
        root_node='order a pizza',
        target_node='root',
        target_insert_as='child',
        source_username=CONVERSATION_USERNAME, 
        source_password=CONVERSATION_PASSWORD, 
        source_workspace=WORKSPACE_ID,
        target_username=CONVERSATION_USERNAME, 
        target_password=CONVERSATION_PASSWORD, 
        target_workspace=TARGET_WORKSPACE,
        version=VERSION,
        target_backup_file='backup/ex4.json')
```

and the projection will look like:

```
root
├── order a pizza (jumps to: kind of pizza)
│   ├── response_condition - @special_type:vegetarian
│   ├── kind of pizza (jumps to: get name)
│   │   ├── event_handler - @special_type:vegetarian
│   │   ├── event_handler
│   │   ├── event_handler
│   │   ├── slot - @special_type != 'vegetarian'
│   │   │   ├── event_handler
│   │   │   ├── event_handler - @pizza_type
│   │   │   ├── event_handler - @pizza_type:deep-dish
│   │   │   ├── event_handler - @pizza_type:thin-crust
│   │   │   └── event_handler - true
│   │   ├── slot - @special_type != 'vegetarian'
│   │   │   ├── event_handler
│   │   │   ├── event_handler - @pizza_topping
│   │   │   ├── event_handler - @pizza_topping:jalapeno
│   │   │   └── event_handler - true
│   │   ├── event_handler
│   │   └── true
│   │       └── slot
│   │           ├── event_handler
│   │           └── event_handler
│   └── response_condition - true
├── welcome
├── 1
├── 2
│   ├── 2_1
│   └── 2_2
├── 3
│   ├── 3_1
│   ├── 3_2
│   └── 3_3
├── get name
│   └── name slot
│       └── slot
│           ├── event_handler - @sys-person
│           └── event_handler
└── Anything else
```


### delete\_branch\_from\_csv

Module: `wcs_deployment_utils.dialog.delete_branch_from_csv`

Iterate through a CSV file and prune dialog tree

A backup will be kept at `target_backup_file`

CSV file will be of the following structure:

`action,id`

valid actions are "REMOVE"

id will refer to either a node ID or a node title

**parameters**:

`conversation_username`: username for WCS instance

`conversation_password`: password for WCS instance

`version`: version of WCS API

`workspace`: workspace for WCS instance

`csv_file`: csv file containing branches to remove

`target_backup_file`: backup workspace at this path

**returns**:

`nodes_removed`: list of (identifier, id) s of nodes removed

`nodes_not_existing`: list of identifiers of nodes not found in target

**Example**:

```
from wcs_deployment_utils.dialog import delete_branch_from_csv

deleted, not_found = delete_branch_from_csv(
    conversation_username=CONVERSATION_USERNAME,
    conversation_password=CONVERSATION_PASSWORD,
    workspace=TARGET_WORKSPACE,
    version=VERSION,
    csv_file='example_data/delete_branch.csv',
    target_backup_file='backup/ex5.json')
```

### copy\_intent\_data

Module: `wcs_deployment_utils.intents.copy_intent_data`

Copy intent data from a WCS workspace to a target workspace.

Copy intent data in an additive pattern from a source workspace to a target workspace. Copy is additive with existing data and will not replace existing data unless clear_existing is specified

**parameters**:

`intent`: name of intent to copy

`source_username`: username for source WCS instance

`source_password`: password for source WCS instance

`source_workspace`: workspace id for source WCS instance

`target_username`: username for target WCS instance

`target_password`: password for target WCS instance

`target_workspace`: workspace id for target WCS instance

`version`: version of WCS instances

`clear_existing`: boolean to clear existing intent data from target

`target_backup_file`: backup existing target workspace to this file

**Example**:

```
from wcs_deployment_utils.intents import copy_intent_data

copy_intent_data(
    intent='order_pizza',
    source_username=CONVERSATION_USERNAME,
    source_password=CONVERSATION_PASSWORD,
    source_workspace=WORKSPACE_ID,
    target_username=CONVERSATION_USERNAME,
    target_password=CONVERSATION_PASSWORD,
    target_workspace=TARGET_WORKSPACE,
    version=VERSION,
    clear_existing=False,
    target_backup_file='backup/ex2.json')
```

### load\_csv\_as\_intent\_data

Module: `wcs_deployment_utils.intents.load_csv_as_intent_data`

Load intent data from a CSV file to a target workspace

CSV file will be of the following structure:
    
`action,intent,example`

valid actions are "ADD" or "REMOVE"

remove statments will be executed first, then adds will be grouped and executed as a single statement. adds are additive with existing data and will not replace existing data unless the 'clear_existing' option is True

**parameters**:

`conversation_username`: username for WCS instance

`conversation_password`: password for WCS instance

`version`: version of WCS API

`workspace`: workspace_id for WCS instance

`csv_file`: CSV file containing data

`clear_existing`: if true, any specified intents that exist will be cleared

`target_backup_file`: backup workspace to this file before making changes

**Example**:

```
from wcs_deployment_utils.intents import load_csv_as_intent_data

load_csv_as_intent_data(
    conversation_username=CONVERSATION_USERNAME,
    conversation_password=CONVERSATION_PASSWORD,
    version=VERSION,
    workspace=TARGET_WORKSPACE,
    csv_file='example_data/intents.csv',
    clear_existing=False,
    target_backup_file='backup/ex1.json')
```

### copy\_entity\_data

`wcs_deployment_utils.entities.copy_entity_data`

Copy entity data from a WCS workspace to a target workspace

Copy entity data in an additive pattern from a source workspace to a target workspace. copy is additive with existing data and will not replace existing data

**parameters**:

`entity`: name of entity to copy

`source_username`: username for source WCS instance

`source_password`: password for source WCS instance

`source_workspace`: workspace id for source WCS instance

`target_username`: username for target WCS instance

`target_password`: password for target WCS instance

`target_workspace`: workspace id for target WCS instance

`version`: version of WCS instances

`clear_existing`: boolean to clear existing intent data from target

`target_backup_file`: backup existing target workspace to this file

**Example**:

```
from wcs_deployment_utils.entities import copy_entity_data

copy_entity_data(
    entity='pizza_topping',
    source_username=CONVERSATION_USERNAME,
    source_password=CONVERSATION_PASSWORD,
    source_workspace=WORKSPACE_ID,
    target_username=CONVERSATION_USERNAME,
    target_password=CONVERSATION_PASSWORD,
    target_workspace=TARGET_WORKSPACE,
    version=VERSION,
    clear_existing=False,
    target_backup_file='backup/ex3.json')
```

### load\_csv\_as\_entity\_data

Module: `wcs_deployment_utils.entities.load_csv_as_entity_data`

Load entity data from a CSV file to a target workspace

Currently can only handle synonym values

CSV file will be of the following structure:

`action,entity,value,synonym`

valid actions are "ADD" or "REMOVE"

remove statments will be executed first, then adds will be grouped and executed as a single statement. adds are additive with existing data and will not replace existing data unless the 'clear_existing' option is True

**parameters**:

`conversation_username`: username for WCS instance

`conversation_password`: password for WCS instance

`version`: version of WCS API

`workspace`: workspace_id for WCS instance

`csv_file`: CSV file containing data

`clear_existing`: if true, any specified intents that exist will be cleared

`target_backup_file`: backup workspace to this file before making changes

**Example**:

```
from wcs_deployment_utils.entities import load_csv_as_entity_data

load_csv_as_entity_data(
    conversation_username=CONVERSATION_USERNAME,
    conversation_password=CONVERSATION_PASSWORD,
    version=VERSION,
    workspace=TARGET_WORKSPACE,
    csv_file='example_data/entities.csv',
    clear_existing=False,
    target_backup_file='backup/ex3.json')
```

### get\_and\_backup\_workspace

Module: `wcs_deployment_utils.util.get_and_backup_workspace`

Gets an export of a workspace and stores it locally

**parameters**:

`username`: WCS username

`password`: WCS password

`workspace`: WCS workspace id

`version`: WCS API version

`export_path`: store export at this path

**returns**:

`export`: dict representation of WCS workspace
  
**Example**:
```
from wcs_deployment_utils.util import get_and_backup_workspace

export = get_and_backup_workspace(
    username=CONVERSATION_USERNAME,
    password=CONVERSATION_PASSWORD,
    workspace=TARGET_WORKSPACE,
    version=VERSION,
    export_path='backup/ex5.json')
```

## Testing

Testing requires `pytest`. 

To execute tests against mock data: `python -m pytest -m mock -v`

To execute tests against live data: `python -m pytest -m live -v`

To execute all tests: `python -m pytest -v`

Live tests will require that credentials are supplied in `test/config/test_credentials.json`. A sample file is provided.

## Planned Roadmap

1. Improve performance and reporting of intents and entities operations
2. Make text based representation of a WCS workspace a standalone function