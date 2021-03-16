#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import toml
import sys
import flask

DEFAULT_ENVIRONMENT = 'development'
CONFIG_FILE_NAME = 'environment.toml'

def get_config_path():
    config_path = os.environ.get('TSOHA_CONFIG', None)

    if config_path:
        return config_path

    checking_directory = os.getcwd()

    while os.path.exists(checking_directory):
        config_path = os.path.join(os.getcwd(), CONFIG_FILE_NAME)

        if os.path.exists(config_path):
            return config_path

        parent = os.path.dirname(checking_directory)

        if parent == checking_directory:
            break

        checking_directory = parent

    return None

def get_config(app=None):
    if app is None:
        env = 'production'
    else:
        env = app.config['ENV']

    config_path = get_config_path()

    if config_path is None:
        print('Failed to find a configuration file!')
        print('Please specify a path using the TSOHA_CONFIG environment variable or')
        print(f'place a file named \'{CONFIG_FILE_NAME}\' somewhere along the current path.')
        sys.exit(1)

    with open(config_path, 'r') as f:
        environments = toml.loads(f.read())

        if app:
            app.config.update(environments[env])

        return environments[env]
