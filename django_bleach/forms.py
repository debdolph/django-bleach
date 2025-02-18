# -*- coding: utf-8 -*-
import bleach

from django import forms
from django.core.exceptions import ImproperlyConfigured

from django.conf import settings
from django.utils.safestring import mark_safe
from importlib import import_module

from django_bleach.utils import get_bleach_default_options


def load_widget(path):
    """ Load custom widget for the form field """
    i = path.rfind(".")
    module, attr = path[:i], path[i + 1:]
    try:
        mod = import_module(module)
    except (ImportError, ValueError) as e:
        error_message = "Error importing widget for BleachField %s: '%s'"
        raise ImproperlyConfigured(error_message % (path, e))

    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            "Module '%s' does not define a '%s' widget" % (module, attr)
        )

    return cls


def get_default_widget():
    """ Get the default widget or the widget defined in settings """
    default_widget = forms.Textarea
    if hasattr(settings, "BLEACH_DEFAULT_WIDGET"):
        default_widget = load_widget(settings.BLEACH_DEFAULT_WIDGET)
    return default_widget


class BleachField(forms.CharField):
    """ Bleach form field """
    empty_values = [None, "", [], (), {}]

    def __init__(self, allowed_tags=None, allowed_attributes=None,
                 allowed_styles=None, allowed_protocols=None,
                 strip_comments=None, strip_tags=None, *args, **kwargs):

        self.widget = get_default_widget()

        super(BleachField, self).__init__(*args, **kwargs)

        self.bleach_options = get_bleach_default_options()

        if allowed_tags is not None:
            self.bleach_options["tags"] = allowed_tags
        if allowed_attributes is not None:
            self.bleach_options["attributes"] = allowed_attributes
        if allowed_styles is not None:
            self.bleach_options["styles"] = allowed_styles
        if allowed_protocols is not None:
            self.bleach_options["protocols"] = allowed_protocols
        if strip_tags is not None:
            self.bleach_options["strip"] = strip_tags
        if strip_comments is not None:
            self.bleach_options["strip_comments"] = strip_comments

    def to_python(self, value):
        """
        Strips any dodgy HTML tags from the input.

        Mark the return value as template safe.
        """
        if value in self.empty_values:
            return self.empty_value
        return mark_safe(bleach.clean(value, **self.bleach_options))
