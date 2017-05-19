# -*- coding: utf-8 -*-
from amplify.agent.collectors.abstract import AbstractMetaCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMPoolMetaCollector(AbstractMetaCollector):
    """
    Meta collector.  Collects meta data about pool
    """
    short_name = 'phpfpm_pool_meta'

    def __init__(self, **kwargs):
        super(PHPFPMPoolMetaCollector, self).__init__(**kwargs)

    @property
    def default_meta(self):
        meta = {
            'type': self.object.type,
            'root_uuid': self.object.root_uuid,
            'local_id': self.object.local_id,
            'name': self.object.name,
            'display_name': self.object.display_name,
            'parent_local_id': self.object.parent_local_id,
            'listen': self.object.listen,
            'flisten': self.object.flisten,
            'status_path': self.object.status_path,
            'can_have_children': False
        }
        return meta
