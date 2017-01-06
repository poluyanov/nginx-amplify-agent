# -*- coding: utf-8 -*-
import re

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


RE_TYPE = type(re.compile('amplify'))


class Filter(object):
    def __init__(self, data=None, metric=None, filter_rule_id=None):
        self.metric = metric
        self.filter_rule_id = filter_rule_id
        self.filename = None
        self.data = {}
        self._negated_conditions = {}

        # normalize vars
        for key, operator, value in data or []:
            if key == 'logname':
                self.filename = value
                continue
            elif key == '$request_method':
                normalized_value = value.upper()
            else:
                normalized_value = value

            # try to treat any value as a regex
            try:
                normalized_value = re.compile(normalized_value)
            except:
                pass

            normalized_key = key.replace('$', '')
            self.data[normalized_key] = normalized_value
            self._negated_conditions[normalized_key] = (operator == '!~')

        self.empty = not self.data and not self.filename

    def match(self, parsed):
        """
        Checks if a parsed string matches a filter
        :param parsed: {} of parsed string
        :return: True of False
        """
        for filter_key, filter_value in self.data.iteritems():
            # if the key isn't in parsed, then it's irrelevant
            if filter_key not in parsed:
                return False

            negated = self._negated_conditions[filter_key]
            value = str(parsed[filter_key])

            string_equals = isinstance(filter_value, str) and filter_value == value
            regex_matches = isinstance(filter_value, RE_TYPE) and bool(re.match(filter_value, value))
            values_match = (string_equals or regex_matches)

            if not values_match and not negated:
                return False
            elif values_match and negated:
                return False

        return True
