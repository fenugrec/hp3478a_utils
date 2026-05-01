#!/usr/bin/env python

# fenugrec 2026, gplv3

# some config class magic based on
# https://alexandra-zaharia.github.io/posts/python-configuration-and-dataclasses/
# modified to use ast.literal_eval() to ~safely convert strings to numeric types when applicable
# idea is to digest a ini-style .conf file into a class whose members can be used like 'cfg.dut.baud'

import ast
import configparser

class DynamicConfig:
    def __init__(self, conf):
        if not isinstance(conf, dict):
            raise TypeError(f'dict expected, found {type(conf).__name__}')

        self._raw = conf
        for key, value in self._raw.items():
            setattr(self, key, ast.literal_eval(value))

class DynamicConfigIni:
    def __init__(self, conf):
        if not isinstance(conf, configparser.ConfigParser):
            raise TypeError(f'ConfigParser expected, found {type(conf).__name__}')

        self._raw = conf
        for key, value in self._raw.items():
            setattr(self, key, DynamicConfig(dict(value.items())))

class magiconfig(DynamicConfigIni):
    def __init__(self, filename):
        self.parser = configparser.ConfigParser()
        self.parser.optionxform = lambda option: option  # hax to make config case-sensitive instead of force-lowercase
        self.parser.read_file(filename)
        super().__init__(self.parser)

# helper func to pretty print config tree
    def print_configtree(self, logger):
        parser = self.parser
        for sec in parser.sections():
            for key in parser[sec]:
                rawval = parser[sec][key]
                logger.info(f'\t{sec}.{key}={rawval}')

