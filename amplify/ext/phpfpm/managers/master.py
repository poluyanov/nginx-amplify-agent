# -*- coding: utf-8 -*-
import hashlib
import psutil

from collections import defaultdict

from amplify.agent.common.context import context
from amplify.agent.common.util import subp
from amplify.agent.managers.abstract import ObjectManager
from amplify.agent.data.eventd import INFO

from amplify.ext.phpfpm.util.ps import PS_CMD, MASTER_PARSER, PS_PARSER
from amplify.ext.phpfpm.util.ps import LS_CMD, LS_PARSER
from amplify.ext.phpfpm.objects.master import PHPFPMObject
from amplify.ext.phpfpm import AMPLIFY_EXT_KEY


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMManager(ObjectManager):
    """
    Manager for php-fpm objects.
    """
    ext = AMPLIFY_EXT_KEY

    name = 'phpfpm_manager'
    type = 'phpfpm'
    types = ('phpfpm',)

    def _discover_objects(self):
        # save the current ids
        existing_hashes = [obj.definition_hash for obj in self.objects.find_all(types=self.types)]

        phpfpm_masters = self._find_all()

        discovered_hashes = []
        while len(phpfpm_masters):
            try:
                data = phpfpm_masters.pop()
                root_uuid = context.objects.root_object.uuid if context.objects.root_object else None
                definition = {'type': 'phpfpm', 'local_id': data['local_id'], 'root_uuid': root_uuid}
                definition_hash = PHPFPMObject.hash(definition)
                discovered_hashes.append(definition_hash)

                if definition_hash not in existing_hashes:
                    # New object -- create it
                    new_obj = PHPFPMObject(data=data)

                    # Send discover event.
                    new_obj.eventd.event(
                        level=INFO,
                        message='php-fpm master process found, pid %s' % new_obj.pid
                    )

                    self.objects.register(new_obj, parent_id=self.objects.root_id)
                elif definition_hash in existing_hashes:
                    for obj in self.objects.find_all(types=self.types):
                        if obj.definition_hash == definition_hash:
                            current_obj = obj
                            break

                    if current_obj.pid != data['pid']:
                        # PIDs changed...php-fpm must have been restarted
                        context.log.debug(
                            'php-fpm was restarted (pid was %s now %s)' % (
                                current_obj.pid, data['pid']
                            )
                        )
                        new_obj = PHPFPMObject(data=data)

                        # send php-fpm restart event
                        new_obj.eventd.event(
                            level=INFO,
                            message='php-fpm master process was restarted, new pid %s, old pid %s' % (
                                new_obj.pid,
                                current_obj.pid
                            )
                        )

                        # stop and unregister children
                        for child_obj in self.objects.find_all(
                                obj_id=current_obj.id,
                                children=True,
                                include_self=False
                        ):
                            child_obj.stop()
                            self.objects.unregister(obj=child_obj)

                        self.objects.unregister(current_obj)  # unregister old object
                        current_obj.stop()  # stop old object

                        self.objects.register(new_obj, parent_id=self.objects.root_id)
            except psutil.NoSuchProcess:
                context.log.debug('phpfpm is restarting/reloading, pids are changing, agent is waiting')

        # check if we left something in objects (phpfpm could be stopped or something)
        dropped_hashes = filter(lambda x: x not in discovered_hashes, existing_hashes)
        if len(dropped_hashes):
            for dropped_hash in dropped_hashes:
                for obj in self.objects.find_all(types=self.types):
                    if obj.definition_hash == dropped_hash:
                        dropped_obj = obj
                        break

            context.log.debug('phpfpm was stopped (pid was %s)' % dropped_obj.pid)

            for child_obj in self.objects.find_all(
                obj_id=dropped_obj.id,
                children=True,
                include_self=False
            ):
                child_obj.stop()
                self.objects.unregister(child_obj)

            dropped_obj.stop()
            self.objects.unregister(dropped_obj)

    @staticmethod
    def _find_all():
        """
        Tries to find a master process

        :return: List of Dicts phpfpm object definitions
        """
        # get ps info
        try:
            ps, _ = subp.call(PS_CMD)
            context.log.debug('ps php-fpm output: %s' % ps)
        except Exception as e:
            # log error
            exception_name = e.__class__.__name__
            context.log.debug('failed to find running php-fpm via "%s" due to %s' % (PS_CMD, exception_name))
            context.log.debug('additional info:', exc_info=True)

            # If there is a root_object defined, log an event to send to the cloud.
            if context.objects.root_object:
                context.objects.root_object.eventd.event(
                    level=INFO,
                    message='no php-fpm found'
                )

            # break processing returning a fault-tolerant empty list
            return []

        # return an empty list if there are no master processes
        if not any('master process' in line for line in ps):
            context.log.info('no php-fpm masters found')

            # break processing returning a fault-tolerant empty list
            return []

        # collect all info about processes
        masters = defaultdict(lambda: defaultdict(list))
        try:
            for line in ps:
                parsed = PS_PARSER(line)

                # if not parsed - go to the next line
                if parsed is None:
                    continue

                pid, ppid, cmd = parsed  # unpack values

                # match master process
                if 'master process' in cmd:

                    # if ppid isn't 1, then the master process must have been started with a launcher
                    if ppid != 1:
                        out, err = subp.call('ps o command %d' % ppid)
                        parent_command = out[1]  # take the second line because the first is a header
                        context.log.debug(
                            'launching php-fpm with "%s" is not currently supported' % parent_command
                        )
                        continue

                    try:
                        conf_path = MASTER_PARSER(cmd)
                    except:
                        context.log.error('failed to find conf_path for %s' % cmd)
                        context.log.debug('additional info:', exc_info=True)
                    else:
                        # calculate local_id
                        local_id = hashlib.sha256('%s_%s' % (cmd, conf_path)).hexdigest()

                        if pid not in masters:
                            # Because of the nested default dict all we have to do is initialize the dict value.
                            masters[pid]

                        masters[pid].update({
                            'cmd': cmd.strip(),
                            'conf_path': conf_path,
                            'pid': pid,
                            'local_id': local_id
                        })
                # match pool process
                elif 'pool' in cmd:
                    masters[ppid]['workers'].append(pid)

            # get the bin path for each master (remember that each worker
            # process will return the bin_path of the master)
            for master in masters.itervalues():
                # if bin_path was found before, skip
                if 'bin_path' in master:
                    continue

                all_pids = [master['pid']] + master['workers']
                last_exception = None
                ls_cmd = LS_CMD % master['pid']

                for pid in all_pids:
                    ls_cmd = LS_CMD % pid
                    try:
                        ls, _ = subp.call(ls_cmd)
                        context.log.debug('ls "%s" output: %s' % (ls_cmd, ls))
                    except Exception as e:
                        last_exception = e
                    else:
                        bin_path = LS_PARSER(ls[0])

                        masters[master['pid']].update({
                            'bin_path': bin_path
                        })

                        last_exception = None  # clear last exception
                        break  # once we find one successful bin_path break

                # if no ls was successful...
                if last_exception:
                    # ...log error
                    exception_name = last_exception.__class__.__name__
                    context.log.error(
                        'failed to find php-fpm bin path, last attempt: '
                        '"%s" failed due to %s' %
                        (ls_cmd, exception_name)
                    )
                    context.log.debug('additional info:', exc_info=True)

                    # If there is a root_object defined, log an event to send to the cloud.
                    if context.objects.root_object:
                        context.objects.root_object.eventd.event(
                            level=INFO,
                            message='php-fpm bin not found'
                        )
        except Exception as e:
            # log error
            exception_name = e.__class__.__name__
            context.log.error('failed to parse ps results due to %s' % exception_name)
            context.log.debug('additional info:', exc_info=True)

        # format results
        results = []
        for payload in masters.itervalues():
            results.append(payload)
        return results
