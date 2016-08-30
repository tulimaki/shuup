# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.text import force_text, slugify


def generate_multilanguage_slugs(object, name_getter, slug_length=128):
    for language_code, language_name in settings.LANGUAGES:
        if not object.has_translation(language_code):
            continue
        try:
            translation = object.get_translation(language_code=language_code)
            translation.refresh_from_db()
        except ObjectDoesNotExist:
            # Guessing the translation is deleted recently so let's just skip this language
            continue

        # Since slugs can be set by the merchant let's not override if already set
        if translation.slug:
            continue
        name = force_text(name_getter(object, translation))
        slug = slugify(name)
        translation.slug = (slug[:slug_length] if slug else None)
        translation.save()
