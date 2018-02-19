"""SETUP"""
from setuptools import setup, find_packages

setup(
    name='wcs-deployment-utils',
    version='0.0.3',
    author='Paul Thoresen',
    author_email='pthoresen@us.ibm.com',
    url='https://github.com/with-watson/wcs-deployment-utils',
    description='a set of utilities for managing deployments of Watson Conversation Service',
    long_description="""\
        wcs-deployment-utils
        ====================

        README and examples available here: https://github.com/with-watson/wcs-deployment-utils/

        A set of utilities to script common Watson Conversation tasks without using the service tooling.

        These are particularly useful if you need to build or apply changes to a set of Watson Conversation instances in an additive, programmatic, and repeatable way. A few examples of useful situations for these utilities:

        - You want to copy a dialog branch from one workspace to another without overwriting the entire dialog tree
        - You want to merge entity definitions from one workspace to another without overwriting existing entity components
        - You want to build a workspace as a set of modular components. (Workspace 1 uses modules A and C, but workspace 2 uses modules B and C)

        Included functions are:

        -wcs_deployment_utils.dialog.copy_dialog_data: Copy a branch of dialog from a source workspace to a target workspace.
        -wcs_deployment_utils.dialog.delete_branch_from_csv: Iterate through a CSV file and prune dialog tree
        -wcs_deployment_utils.intents.copy_intent_data: Copy intent data from a WCS workspace to a target workspace.
        -wcs_deployment_utils.intents.load_csv_as_intent_data: Load intent data from a CSV file to a target workspace.
        -wcs_deployment_utils.entities.copy_entity_data: Copy entity data from a WCS workspace to a target workspace
        -wcs_deployment_utils.entities.load_csv_as_entity_data: Load entity data from a CSV file to a target workspace
        -wcs_deployment_utils.util.get_and_backup_workspace: Gets an export of a workspace and stores it locally

        """,
    packages=find_packages(exclude=["test"]),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities"
        ],
    install_requires=[
        'watson_developer_cloud>=1.0.2',
        'pandas>=0.20.0',
        'requests>=2.8.0',
        'anytree>=2.4.3'
    ],
    keywords='wcs watson conversation dialog intent entity intents entities copy deployment'
)
