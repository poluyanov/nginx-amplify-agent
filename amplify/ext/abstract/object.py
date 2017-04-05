# -*- coding: utf-8 -*-
import abc
from collections import defaultdict

from amplify.agent.common.context import context
from amplify.agent.common.util.host import hostname
from amplify.agent.objects.abstract import AbstractObject as BaseObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class AbstractObject(BaseObject):
    type = 'abstract'

    def __init__(self, *args, **kwargs):
        super(AbstractObject, self).__init__(*args, **kwargs)

        _interval_dict = defaultdict(lambda: 10)
        _interval_dict['default']  # _interval_dict['default'] = 10
        self.intervals = context.app_config['containers'].get(self.type, {}).get('poll_intervals', _interval_dict)

    @property
    def root_uuid(self):
        """
        General base method for returning the root_uuid.
        """
        return context.objects.root_object.uuid if context.objects.root_object else None

    @abc.abstractproperty
    def local_id_args(self):
        """
        Abstract enforcement for SDK inherited objects.  These arguments are used to create the local_id hash used in
        the object definition hash.
        """
        return super(AbstractObject, self).local_id_args

    @property
    def definition(self):
        return {'type': self.type, 'local_id': self.local_id, 'root_uuid': self.root_uuid}

    @property
    def name(self):
        """
        Generic attribute wrapper for returning object names.  Has a sensible default if private "._name" attribute is
        not defined.
        """
        return self._name if getattr(self, "_name", None) is not None else "%s @ %s" % (self.type, hostname())
