# -*- coding: utf-8 -*-
import glob
import copy
from io import BytesIO
from ConfigParser import ConfigParser

from amplify.agent.common.context import context

from amplify.agent.common.util.sfile import StringFile


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov",
    "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMConfig(object):
    """
    An in memory representation of a PHPFPM config file.  Provides a convenient
    object for handling of parsing and representation of a PHPFPM config.

    Consider usage similar to ConfigParser.ConfigParser().
    """
    def __init__(self, path=None):
        """
        :param path: String Optional config path.  If provided parsing will be
                     done during init process.
        """
        self.path = path  # path to phpfpm file
        self._results = {
            'file': self.path,
            'include': [],
            'pools': []
        }  # parsed result dict

        if self.path is not None:
            self.read(self.path)

    @property
    def parsed(self):
        return self._results

    def get(self, *args):
        def _recursive_dict_lookup(_itm=None, *args):
            """
            Takes an unbounded list of keys and traverses a dict in a nested
            fashion to return the ending value map from the key chain.

            ex::
                PHPFPMConfig.get('global', 'includes')
                returns dict.get('global').get('includes')
            """
            # if _itm is None set it to top results
            if _itm is None:
                _itm = copy.deepcopy(self._results)

            _itm = _itm.get(args[0])

            if len(args[1:]) > 0:
                _itm = _recursive_dict_lookup(*args[1:], _itm=_itm)

            return _itm

        return self._recursive_dict_lookup(*args)

    def _parse(self, sfile):
        pos = 0
        for line in sfile:
            if line.startswith('['):
                # found the first named block
                break
            elif line.startswith('include'):
                include_rule = line.split('=', 1)[-1].strip()
                self._results['include'].append(include_rule)

            pos += 1

        # create a concatenated string buffer for building a trimeed file obj
        concat_str = '\n'.join(sfile[pos:])

        # parse root config
        try:
            root_config = ConfigParser()
            # readfp for readlines interface for reading in memory buffer
            root_config.readfp(BytesIO(concat_str), self.path)

            self._results['include'].append(
                root_config.get('global', 'include')
            )
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error(
                'failed to parse php-fpm master config %s due to %s' % (
                    self.path,
                    exception_name
                )
            )
            context.log.debug('additional info:', exc_info=True)

        # find included configs (pools)
        included = []
        for include_rule in self._results['include']:
            if '*' in include_rule:
                for filepath in glob.glob(include_rule):
                    included.append(filepath)

        # parse included configs (pools)
        for filepath in included:
            pool = {
                'file': filepath,
                'name': None,
                'listen': None,
                'status_path': None
            }
            try:
                pool_config = ConfigParser()
                pool_config.read(filepath)

                pool_name = pool_config.sections()[0]
                pool['name'] = pool_name

                listen = pool_config.get(pool_name, 'listen')
                pool['listen'] = listen

                status_path = pool_config.get(pool_name, 'pm.status_path')
                pool['status_path'] = status_path
            except Exception as e:
                exception_name = e.__class__.__name__
                context.log.error('failed to parse php-fpm pool config %s due to %s' % (filepath, exception_name))
                context.log.debug('additional info:', exc_info=True)
            else:
                # only add pool if there is no error and if pool is properly
                self._results['pools'].append(pool)

    def read(self, path):
        """
        Open a file, load it into a string buffer and parse it.
        """
        with StringFile() as sfile:  # open in memory string file

            # open the config file and write each line into the string file
            with open(path, 'r') as config:
                for line in config:
                    sfile.write(line)

            self._parse(sfile)

    def readb(self, buffer):
        """
        Read a string-castable buffer instead of opening a file.  Useful for
        testing.
        """
        with StringFile(str(buffer)) as sfile:
            self._parse(sfile)
