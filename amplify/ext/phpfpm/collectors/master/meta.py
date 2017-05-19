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


class PHPFPMMetaCollector(AbstractMetaCollector):
    """
    Meta collector.  Collects meta data about master
    """
    short_name = 'phpfpm_meta'

    def __init__(self, **kwargs):
        super(PHPFPMMetaCollector, self).__init__(**kwargs)

        self.register(
            self.version
        )

    @property
    def default_meta(self):
        meta = {
            'type': self.object.type,
            'root_uuid': self.object.root_uuid,
            'local_id': self.object.local_id,
            'name': self.object.name,
            'display_name': self.object.display_name,
            'cmd': self.object.cmd,
            'conf_path': self.object.conf_path,
            'workers': len(self.object.workers),
            'bin_path': self.object.bin_path,
            'version': None
        }

        if not self.in_container:
            meta['pid'] = self.object.pid

        return meta

    def version(self):
        if self.object.bin_path is not None:
            exe_name = self.object.bin_path.split('/')[-1]

            # pull out specific characters
            version = filter(lambda char: char.isdigit() or char == '.', exe_name)

            self.meta['version'] = version
