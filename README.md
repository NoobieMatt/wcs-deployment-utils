# Watson Conversation Deployment Utilities

A set of utilities to script common Watson Conversation tasks without using the service tooling.

These are particularly useful if you need to build or apply changes to a set of Watson Conversation instances in an additive, programmatic, and repeatable way. A few examples of useful situations for these utilities:

1. You want to copy a dialog branch from one workspace to another without overwriting the entire dialog tree
2. You want to merge entity definitions from one workspace to another without overwriting existing entity components
3. You want to build a workspace as a set of modular components. (Workspace 1 uses modules A and C, but workspace 2 uses modules B and C)


## Directory Structure

These scripts are designed around a loosely enforced directory structure. In general, the following directory structure is recommended for these scripts:

```
Utility root
|
|--- common                        common script functions
|   |   load_intent_data.py        common script function implementation
|   |   ...
|   
|--- composite                     composite scripts
|   |   add_test_module.py         composite script
|   
|--- actions
|   |  
|   |---load_csv_as_intent_data    actions for a common script function
|   |    |  
|   |    |--- test
|   |        |
|   |        |   config.json       configuration files required for this action
|   |        |   examples.csv
|   |  ...   |   ...
```

### Common Script Function
The common script functions are included in a `common` directory. These are the generic scripts that define specific operations that can be performed

### Actions
The scripts use a concept called actions to organize local configuration and data. Certain functions make use of data stored locally, so this directory provides a consistent structure for managing these files. **Not all scripts will require local configuration and data**

The expected content of an action directory is specified in the definition of the function. Different scripts will require different data to be present.

It's recommended that action files (data and configuration) are placed in `<root>/actions/<common function name>/<action name>`. In this example, the `test` action has been defined for the `load_csv_as_intent_data` function.

Inside of the `load_csv_as_intent_data` function, a developer can reference the `test` action and the function will pull its configuration information from the corresponding directory.

These scripts include a `root_dir` argument to allow a developer to specify the location of this `action` directory.

Sample actions are included in the `assets` directory

### Composite Scripts
Often, it takes a set of operations to produce a meaningful output in a workspace. For instance, when a dialog branch is copied, it may require a set of specific intents and entities in order to function. The composite script directory is recommended for these discrete groupings of operations.

It's recommended that the composite scripts are placed in `<root>/composite` and named according to the task performed.

A sample composite script is included in the `assets` directory


## Included Functions

### copy\_dialog\_data

Copy a branch of dialog from a source workspace to a target workspace.

Default insert is 'sibling' which inserts the branch as the immediate
sibling of the target node. Alternatively, 'child' can be specified
so that the branch is inserted as the first child of the node. If
`target_node` is specified as 'root', the branch is inserted as the first
child of the dialog root

Any existing nodes with the same name or ID will be deleted

These options are summarized below

```
Dialog Root
|
|<-(insert as root)
|
|--Existing Node
        | 
        |<-(insert as child)
        |
        | Existing Child Node
|
|<-(insert as sibling)
...
```

Parameters:
`root_node`: ID or title of the root node in source
`target_node`: ID or title of the root node in target
`target_insert_as`: Default 'sibling'. Location of branch insertion, with 
    respect to the target root. Valid options are 'sibling', 'child' or 'root'
`source_username`: Username for source WCS instance
`source_password`: Password for source WCS instance
`source_workspace`: Workspace ID for source WCS instance
`target_username`: Username for target WCS instance
`target_password`: Password for target WCS instance
`target_workspace`: Workspace ID for target WCS instance
`version`: WCS API version

Example:

```
copy_dialog_data(root_node='order a pizza',
                 target_node='root',
                 target_insert_as='sibling',
                 target_username=CONVERSATION_USERNAME, 
                 target_password=CONVERSATION_PASSWORD, 
                 target_workspace=TARGET_WORKSPACE,
                 source_username=CONVERSATION_USERNAME, 
                 source_password=CONVERSATION_PASSWORD, 
                 source_workspace=WORKSPACE_ID,
                 version=VERSION)
```

### delete\_branch\_from\_csv

Iterate through a CSV file and prune dialog tree from specified root 

CSV file will be of the following structure:
`action,id`

valid actions are "REMOVE"

id will refer to either a node ID or a node title

CSV file is located at: 
`{rootdir}/actions/delete_branch_from_csv/{action}/nodes.csv`

Parameters:
`conversation_username`: username for WCS instance
`conversation_password`: password for WCS instance
`version`: version of WCS API
`workspace_id`: workspace_id for WCS instance
`action`: directory containing nodes.csv
`root_dir`: root directory containing actions directory

Example:

```
delete_branch_from_csv(
    conversation_username=CONVERSATION_USERNAME,
    conversation_password=CONVERSATION_PASSWORD,
    version=VERSION,
    workspace_id=TARGET_WORKSPACE,
    action='pizza',
    root_dir='.')
```

### copy\_intent\_data

Copy intent data from a WCS workspace

Copy intent data in an additive pattern from a source workspace
to a target workspace. copy is additive with existing
data and will not replace existing data unless `clear_existing` is
`True`

parameters:
`intent`: name of intent to copy
`source_username`: username for source WCS instance
`source_password`: password for source WCS instance
`source_workspace`: workspace id for source WCS instance
`target_username`: username for target WCS instance
`target_password`: password for target WCS instance
`target_workspace`: workspace id for target WCS instance
`version`: version of WCS instances
`clear_existing`: boolean to clear existing intent data from target

Example:

```
copy_intent_data(intent='order_pizza',
                 target_username=CONVERSATION_USERNAME, 
                 target_password=CONVERSATION_PASSWORD, 
                 target_workspace=TARGET_WORKSPACE,
                 source_username=CONVERSATION_USERNAME, 
                 source_password=CONVERSATION_PASSWORD, 
                 source_workspace=WORKSPACE_ID,
                 version=VERSION,
                 clear_existing=False)
```

### load\_csv\_as\_intent\_data

Load intent data from a CSV file

CSV file will be of the following structure:
`action,intent,example`

valid actions are "ADD" or "REMOVE"

CSV file is located at: 
`{rootdir}/actions/load_csv_as_intent_data/{action}/examples.csv`

an optional config file is located at:
`{rootdir}/actions/load_csv_as_intent_data/{action}/config.json`

this config file can specify a single configuration option at the
moment, `clear_existing`: (Boolean)

remove statments will be executed first, then adds will be grouped
and executed as a single statement. adds are additive with existing
data and will not replace existing data unless `clear_existing` is
`True`

parameters:
`conversation_username`: username for WCS instance
`conversation_password`: password for WCS instance
`version`: version of WCS API
`workspace_id`: workspace_id for WCS instance
`action`: directory containing examples.csv
`root_dir`: root directory containing actions directory

Example:

```
load_csv_as_intent_data(conversation_username=CONVERSATION_USERNAME,
                 conversation_password=CONVERSATION_PASSWORD,
                 version=VERSION,
                 workspace_id=TARGET_WORKSPACE,
                 action='test',
                 root_dir='.')
```

### copy\_entity\_data

Copy entity data from a WCS workspace

Copy entity data in an additive pattern from a source workspace
to a target workspace. copy is additive with existing
data and will not replace existing data unless `clear_existing` is
`True`

parameters:
`entity`: name of entity to copy
`source_username`: username for source WCS instance
`source_password`: password for source WCS instance
`source_workspace`: workspace id for source WCS instance
`target_username`: username for target WCS instance
`target_password`: password for target WCS instance
`target_workspace`: workspace id for target WCS instance
`version`: version of WCS instances
`clear_existing`: boolean to clear existing intent data from target

Example:

```
copy_entity_data(entity='pizza_topping',
                 target_username=CONVERSATION_USERNAME, 
                 target_password=CONVERSATION_PASSWORD, 
                 target_workspace=TARGET_WORKSPACE,
                 source_username=CONVERSATION_USERNAME, 
                 source_password=CONVERSATION_PASSWORD, 
                 source_workspace=WORKSPACE_ID,
                 version=VERSION,
                 clear_existing=False)
```

### load\_csv\_as\_entity\_data

Load entity data from a CSV file

Currently can only handle synonym values 

CSV file will be of the following structure:
`action,entity,value,synonym`

valid actions are "ADD" or "REMOVE"

CSV file is located at: 
`{rootdir}/actions/load_csv_as_entity_data/{action}/entities.csv`

an optional config file is located at:
`{rootdir}/actions/load_csv_as_entity_data/{action}/config.json`

this config file can specify a single configuration option at the
moment, `clear_existing`: (Boolean)

remove statments will be executed first, then adds will be grouped
and executed as a single statement. adds are additive with existing
data and will not replace existing data unless `clear_existing` is
`True`

parameters:
`conversation_username`: username for WCS instance
`conversation_password`: password for WCS instance
`version`: version of WCS API
`workspace_id`: workspace_id for WCS instance
`action`: directory containing entities.csv
`root_dir`: root directory containing actions directory

Example:

```
load_csv_as_entity_data(conversation_username=CONVERSATION_USERNAME,
                        conversation_password=CONVERSATION_PASSWORD,
                        version=VERSION,
                        workspace_id=TARGET_WORKSPACE,
                        action='test',
                        root_dir='.')
```

## Planned Roadmap

1. Automated Backup -- suitable for `cron`