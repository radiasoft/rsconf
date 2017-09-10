# -*- coding: utf-8 -*-
u"""Load components

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


def import_module(name):
    """Load component

    Args:
        name (str): component to load
    Returns:
        module: component instance
    """
    import importlib

    return importlib.import_module('.' + name, __name__)
