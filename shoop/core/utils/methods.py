# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.core.models import ConstantPrice

def ordered_methods(shop, methods):
    return methods


def get_available_methods(cls, source):
    return ordered_methods(source.shop, [m for m in cls.objects.all() if m.is_available(source)])


def get_all_business_logic_classes():
    # TODO: Add provided business logic
    return [ConstantPrice]


def get_business_logic_choices(empty_label=None):
    choices = []
    for cls in get_all_business_logic_classes():
        choices.append((cls.identifier, cls.name))
    return [(None, "---")] + choices


def get_business_logic_class_for_identifier(identifier):
    for cls in get_all_business_logic_classes():
        if cls.identifier == identifier:
            return cls


