# -*- coding: utf-8 -*-
import glob
import os
import re
from itertools import izip

from pyparsing import (
    Regex, Keyword, Literal, Word, alphanums, CharsNotIn, Forward, Group,
    Optional, OneOrMore, ZeroOrMore, pythonStyleComment, lineno,
    oneOf, QuotedString, nestedExpr, ParseResults
)

from amplify.agent.common.context import context
from amplify.agent.common.util.escape import prep_raw


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Paul McGuire", "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev",
    "Grant Hulegaard"
]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


IGNORED_DIRECTIVES = [
    'ssl_certificate_key',
    'ssl_client_certificate',
    'ssl_password_file',
    'ssl_stapling_file',
    'ssl_trusted_certificate',
    'auth_basic_user_file',
    'secure_link_secret'
]


def set_line_number(input_string, location, tokens):
    # check and limit CPU usage
    context.check_and_limit_cpu_consumption()

    if len(tokens) == 1:
        line_number = lineno(location, input_string)
        NginxConfigParser.tokens_cache[tokens[0]] = line_number
        tokens.line_number = line_number
    else:
        for item in tokens:
            tokens.line_number = NginxConfigParser.tokens_cache.get(item)


class NginxConfigParser(object):
    """
    Nginx config parser originally based on https://github.com/fatiherikli/nginxparser

    Heavily customized and extended by Amplify team.

    Optimized by Paul McGuire author of the pyparsing library (https://www.linkedin.com/in/ptmcg).  Paul's
    optimizations (with minor compatibility tweaks during incorporation by Amplify team) resulted in over a 50%
    performance improvement (~59%).

    Parses single file into json structure
    """
    tokens_cache = {}

    max_size = 20*1024*1024  # 20 mb

    # constants
    left_brace = Literal("{").suppress()
    right_brace = Literal("}").suppress()
    semicolon = Literal(";").suppress()

    # keywords
    IF, SET, REWRITE, PERL_SET, LOG_FORMAT, ALIAS, RETURN, ERROR_PAGE, MAP, SERVER_NAME, SUB_FILTER, ADD_HEADER = (
        map(
            lambda x: x.setParseAction(set_line_number),
            map(
                Keyword,
                "if set rewrite perl_set log_format alias return "
                "error_page map server_name sub_filter add_header".split()
            )
        )
    )

    # string helpers
    string = (
        QuotedString("'", escChar='\\') |
        QuotedString('"', escChar='\\')
    ).setParseAction(set_line_number)

    multiline_string = (
        QuotedString("'", escChar='\\', multiline=True) |
        QuotedString('"', escChar='\\', multiline=True)
    ).setParseAction(set_line_number)

    multiline_string_keep_quotes = (
        QuotedString("'", escChar='\\', multiline=True, unquoteResults=False) |
        QuotedString('"', escChar='\\', multiline=True, unquoteResults=False)
    ).setParseAction(set_line_number)

    # lua keys
    start_with_lua_key = Regex(r'lua_\S+').setParseAction(set_line_number)
    contains_by_lua_key = Regex(r'\S+_by_lua\S*').setParseAction(set_line_number)

    key = (
        ~MAP & ~ALIAS & ~PERL_SET & ~IF & ~SET & ~REWRITE & ~SERVER_NAME & ~SUB_FILTER & ~ADD_HEADER
    ) + Word(alphanums + '$_:%?"~<>\/-+.,*()[]"' + "'").setParseAction(set_line_number)

    # values
    value_one = Regex(r'[^{};]*"[^\";]+"[^{};]*')
    value_two = Regex(r'[^{};]*\'[^\';]+\'')
    value_three = Regex(r'[^{};]+((\${[\d|\w]+(?=})})|[^{};])+')
    value_four = Regex(r'[^{};]+(?!${.+})')
    value = (string | value_one | value_two | value_three | value_four).setParseAction(set_line_number)
    rewrite_value = CharsNotIn(";").setParseAction(set_line_number)
    any_value = CharsNotIn(";").setParseAction(set_line_number)
    non_space_value = Regex(r'[^\'\";\s]+').setParseAction(set_line_number)
    if_value = nestedExpr().setParseAction(set_line_number)  # Regex(r'\(.*\)')
    strict_value = CharsNotIn("{};").setParseAction(set_line_number)
    sub_filter_value = (non_space_value | multiline_string_keep_quotes).setParseAction(set_line_number)
    add_header_value = Regex(r'[^{};]*"[^"]+"').setParseAction(set_line_number)
    map_value = (string | Regex(r'((\\\s|[^{};\s])*)')).setParseAction(set_line_number)

    # modifier for location uri [ = | ~ | ~* | ^~ ]
    modifier = oneOf("= ~* ~ ^~")

    assignment = (
        key + Optional(OneOrMore(value + Optional(value))) + semicolon
    ).setParseAction(set_line_number)

    set = (
        SET + any_value + semicolon
    ).setParseAction(set_line_number)

    rewrite = (
        REWRITE + rewrite_value + semicolon
    ).setParseAction(set_line_number)

    perl_set = (
        PERL_SET + key + multiline_string + semicolon
    ).setParseAction(set_line_number)

    lua_content = (
        (start_with_lua_key | contains_by_lua_key) + multiline_string + semicolon
    ).setParseAction(set_line_number)

    alias = (
        ALIAS + any_value + semicolon
    ).setParseAction(set_line_number)

    return_ = (
        (RETURN | ERROR_PAGE) + value + Optional(any_value) + semicolon
    ).setParseAction(set_line_number)

    log_format = (
        LOG_FORMAT + strict_value + any_value + semicolon
    ).setParseAction(set_line_number)

    server_name = (
        SERVER_NAME + any_value + semicolon
    ).setParseAction(set_line_number)

    sub_filter = (
        SUB_FILTER + sub_filter_value + sub_filter_value + semicolon
    ).setParseAction(set_line_number)

    add_header = (
        ADD_HEADER + (non_space_value | string) +
        Optional(multiline_string_keep_quotes | add_header_value | non_space_value) +
        Optional(value) +
        semicolon
    ).setParseAction(set_line_number)

    # script
    map_block = Forward()
    map_block << Group(
        Group(
            MAP + map_value + map_value
        ).setParseAction(set_line_number) +
        left_brace +
        Group(
            ZeroOrMore(
                Group(map_value + Optional(map_value) + semicolon)
            ).setParseAction(set_line_number)
        ) +
        right_brace
    )

    block = Forward()
    block << Group(
        (
            Group(
                key + Optional(modifier) +
                Optional(value + Optional(value))
            ) |
            Group(IF + if_value)
        ).setParseAction(set_line_number) +
        left_brace -  # <----- use '-' operator instead of '+' to get better error messages
        Group(
            ZeroOrMore(
                Group(add_header) | Group(log_format) | Group(lua_content) | Group(perl_set) |
                Group(set) | Group(rewrite) | Group(alias) | Group(return_) |
                Group(assignment) | Group(server_name) | Group(sub_filter) |
                map_block | block
            ).setParseAction(set_line_number)
        ).setParseAction(set_line_number) +
        right_brace
    )

    script = OneOrMore(
        Group(add_header) | Group(server_name) |
        Group(log_format) | Group(perl_set) | Group(lua_content) | Group(alias) | Group(return_) |
        Group(assignment) | Group(set) | Group(rewrite) | Group(sub_filter) |
        map_block | block
    ).ignore(pythonStyleComment)

    INCLUDE_RE = re.compile(r'[^#]*include\s+(?P<include_file>.*);')
    SSL_CERTIFICATE_RE = re.compile(r'[^#]*ssl_certificate\s+(?P<cert_file>.*);')

    def __init__(self, filename='/etc/nginx/nginx.conf'):
        self.filename = filename
        self.folder = os.path.dirname(self.filename)  # stores path to folder with main config
        self.files = {}  # to prevent cycle files and line indexing
        self.directories = {}
        self.parsed_cache = {}  # to cache multiple includes
        self.broken_files = set()  # to prevent reloading broken files
        self.broken_directories = set()  # to prevent reloading broken directories
        self.index = []  # stores index for all sections (points to file number and line number)
        self.ssl_certificates = []
        self.errors = []
        self.tree = {}
        self.directory_map = {}

        self.file_errors = []  # For broken files
        self.directory_errors = []  # for broken directories

    def parse(self):
        NginxConfigParser.tokens_cache = {}
        self.directories, self.files, self.parsed_cache = {}, {}, {}  # drop results from the previous run
        self.tree = self.__logic_parse(self.__pyparse(self.filename))  # parse
        self.construct_directory_map()  # construct a tree of structure
        self.parsed_cache = {}  # drop cached, as it is no longer needed

    @staticmethod
    def get_filesystem_info(path):
        """
        Returns file/folder size, mtime and permissions

        :param path: str path to file/folder
        :return: int, int, str - size, mtime, permissions
        """
        size, mtime, permissions = 0, 0, '0000'

        try:
            size = os.path.getsize(path)
            mtime = int(os.path.getmtime(path))
            permissions = oct(os.stat(path).st_mode & 0777)
        except Exception, e:
            exception_name = e.__class__.__name__
            message = 'failed to stat %s due to: %s' % (path, exception_name)
            context.log.debug(message, exc_info=True)

        return size, mtime, permissions

    def resolve_local_path(self, path):
        """
        Resolves local path
        :param path: str path
        :return: absolute path
        """
        result = path.replace('"', '')
        if not result.startswith('/'):
            result = '%s/%s' % (self.folder, result)
        return result

    @staticmethod
    def resolve_directory(path):
        """
        Returns the dirname of a path.
        """
        return os.path.dirname(path) + os.path.sep

    def populate_directories(self, path):
        """
        Populates self.directories with a directory for a path

        :param path: path to a file
        """
        def populate_directory(dir_path):
            if dir_path not in self.directories:
                try:
                    size, mtime, permissions = self.get_filesystem_info(dir_path)
                    self.directories[dir_path] = {
                        'size': size,
                        'mtime': mtime,
                        'permissions': permissions
                    }

                    # try to list dir - maybe we can get an error on that
                    os.listdir(dir_path)

                except Exception as e:
                    exception_name = e.__class__.__name__
                    exception_message = e.strerror if hasattr(e, 'strerror') else e.message
                    message = 'failed to read %s due to: %s' % (directory_path, exception_name)
                    context.log.debug(message, exc_info=True)
                    self.errors.append(message)
                    self.broken_directories.add(dir_path)
                    self.directory_errors.append((exception_name, exception_message))

        # store directory results
        directory_path = self.resolve_directory(path)
        if '*' in directory_path:
            for path in glob.glob(directory_path):
                populate_directory(path)
        else:
            populate_directory(directory_path)

    def resolve_includes(self, path):
        """
        Takes include path and returns all included files
        Also populates directories

        :param path: str path
        :return: [] of str file names
        """
        # resolve local paths
        path = self.resolve_local_path(path)

        # load all files
        result = []
        if '*' in path:
            for filename in glob.glob(path):
                result.append(filename)
        else:
            result.append(path)

        self.populate_directories(path)
        return result

    def get_structure(self, include_ssl_certs=False):
        """
        Tries to collect all included files, folders and ssl certs and return
        them as dict with mtimes, sizes and permissions.
        Later this dict will be used to determine if a config was changed or not.

        We don't use md5 or other hashes, because it takes time and we should be able
        to run these checks every 20 seconds or so

        :param include_ssl_certs: bool - include ssl certs  or not
        :return: {}, {} - files, directories
        """
        files_result = {}

        # collect all files
        def lightweight_include_search(include_files):
            for file_path in include_files:
                if file_path in files_result:
                    continue
                files_result[file_path] = None
                try:
                    for line in open(file_path):
                        if 'include' in line:
                            gre = self.INCLUDE_RE.match(line)
                            if gre:
                                new_includes = self.resolve_includes(gre.group('include_file'))
                                lightweight_include_search(new_includes)
                        elif include_ssl_certs and 'ssl_certificate' in line:
                            gre = self.SSL_CERTIFICATE_RE.match(line)
                            if gre:
                                cert_file_path = self.resolve_local_path(gre.group('cert_file'))
                                files_result[cert_file_path] = None
                                self.populate_directories(cert_file_path)
                except Exception as e:
                    exception_name = e.__class__.__name__
                    message = 'failed to read %s due to: %s' % (file_path, exception_name)
                    context.log.debug(message, exc_info=True)

        lightweight_include_search(self.resolve_includes(self.filename))

        # get mtimes, sizes and permissions
        for file_path in files_result.iterkeys():
            size, mtime, permissions = self.get_filesystem_info(file_path)
            files_result[file_path] = {
                'size': size,
                'mtime': mtime,
                'permissions': permissions
            }

        return files_result, self.directories

    def __pyparse(self, path):
        """
        Loads and parses all files

        :param path: file path (can contain *)
        """
        result = {}

        for file_path in self.resolve_includes(path):
            # skip files we couldn't read, etc
            if file_path in self.broken_files:
                continue

            if file_path not in self.files:
                # read file contents
                try:
                    size, mtime, permissions = self.get_filesystem_info(file_path)
                    if size > self.max_size:
                        self.errors.append('failed to read %s due to: too large, %s bytes' % (file_path, size))
                        self.broken_files.add(file_path)
                        self.file_errors.append(('NaasException', 'too large, %s bytes' % size))
                        continue

                    source = open(file_path).read()
                    lines_count = source.count('\n')
                except Exception as e:
                    exception_name = e.__class__.__name__
                    exception_message = e.strerror if hasattr(e, 'strerror') else e.message
                    message = 'failed to read %s due to: %s' % (file_path, exception_name)
                    self.errors.append(message)
                    self.broken_files.add(file_path)
                    self.file_errors.append((exception_name, exception_message))
                    context.log.error(message)
                    context.log.debug('additional info:', exc_info=True)
                    continue
                else:
                    # store the results
                    file_index = len(self.files)

                    self.files[file_path] = {
                        'index': file_index,
                        'lines': lines_count,
                        'size': size,
                        'mtime': mtime,
                        'permissions': permissions
                    }

                # Replace windows line endings with unix ones
                source = source.replace('\r\n', '\n')

                # check that file contains some information (not commented)
                all_lines_commented = True
                for line in source.split('\n'):
                    line = line.replace(' ', '')
                    if line and not line.startswith('#'):
                        all_lines_commented = False
                        break

                if all_lines_commented:
                    continue

                try:
                    parsed = list(self.script.parseString(source, parseAll=True))
                except Exception as e:
                    exception_name = e.__class__.__name__
                    message = 'failed to parse %s due to %s' % (file_path, exception_name)
                    self.broken_files.add(file_path)
                    self.errors.append(message)
                    context.log.error(message)
                    context.log.debug('additional info:', exc_info=True)
                    continue

                self.parsed_cache[file_index] = parsed[:]
                result[file_index] = parsed
            else:
                # if we already have the file parsed
                file_index = self.files[file_path]['index']
                result[file_index] = self.parsed_cache.get(file_index, [])

        return result

    def __logic_parse(self, files, result=None):
        """
        Parses input files and updates result dict

        :param files: dict of files from pyparsing
        :return: dict of config tree
        """
        if result is None:
            result = {}

        for file_index, rowsp in files.iteritems():
            rows = rowsp[:]
            while len(rows):
                row = rows.pop(0)
                row_as_list = row.asList()

                if isinstance(row_as_list[0], list):
                    # this is a new key
                    key_bucket, value_bucket = row
                    key = key_bucket[0]

                    if len(key_bucket) == 1:
                        # simple key, with one param
                        subtree_indexed = self.__idx_save(
                            self.__logic_parse({file_index: row[1]}),
                            file_index, row.line_number
                        )
                        if key == 'server':
                            # work with servers
                            if key in result:
                                result[key].append(subtree_indexed)
                            else:
                                result[key] = [subtree_indexed]
                        else:
                            result[key] = subtree_indexed
                    else:
                        # compound key (for locations and upstreams for example)

                        def flatten(l):
                            """Helper function that flattens a list of lists into a single list"""
                            flattened = []
                            for element in l:
                                if not isinstance(element, list):
                                    flattened.append(element)
                                elif isinstance(element, ParseResults):
                                    flattened += flatten(element.asList())
                                else:
                                    flattened += flatten(element)
                            return flattened

                        # with some changes to how we use pyparse we now might get "ParseResults" back...handle it here
                        # typically occurs on "if" statements/blocks
                        if not isinstance(key_bucket[1], (str, unicode)):
                            key_bucket = key_bucket.asList() if isinstance(key_bucket, ParseResults) else key_bucket
                            parse_results = key_bucket.pop()
                            key_bucket += flatten(parse_results)

                        # remove all redundant spaces
                        parts = filter(len, ' '.join(key_bucket[1:]).split(' '))
                        sub_key = ' '.join(parts)

                        subtree_indexed = self.__idx_save(
                            self.__logic_parse({file_index: row[1]}),
                            file_index, row.line_number
                        )

                        if key in result:
                            result[key][sub_key] = subtree_indexed
                        else:
                            result[key] = {sub_key: subtree_indexed}
                else:
                    # can be just an assigment, without value
                    if len(row) >= 2:
                        key, value = row[0], '/s/'.join(row[1:])  # add special "spacer" character combination
                        # this special spacer only is appears in complex "add_header" directives at the moment
                    else:
                        key, value = row[0], ''

                    # transform multiline values to single one
                    if """\'""" in value or """\n""" in value:
                        value = re.sub(r"\'\s*\n\s*\'", '', value)
                        value = re.sub(r"\'", "'", value)

                    # remove spaces
                    value = value.strip()

                    if key in IGNORED_DIRECTIVES:
                        continue  # Pass ignored directives.
                    elif key == 'log_format':
                        # work with log formats
                        gwe = re.match("([\w\d_-]+)\s+'(.+)'", value)
                        if gwe:
                            format_name, format_value = gwe.group(1), gwe.group(2)

                            indexed_value = self.__idx_save(format_value, file_index, row.line_number)
                            # Handle odd Python auto-escaping of raw strings when packing/unpacking.
                            indexed_value = (prep_raw(indexed_value[0]), indexed_value[1])

                            if key in result:
                                result[key][format_name] = indexed_value
                            else:
                                result[key] = {format_name: indexed_value}
                    elif key == 'include':
                        indexed_value = self.__idx_save(value, file_index, row.line_number)

                        if key in result:
                            result[key].append(indexed_value)
                        else:
                            result[key] = [indexed_value]

                        included_files = self.__pyparse(value)
                        self.__logic_parse(included_files, result=result)
                    elif key in ('access_log', 'error_log'):
                        value = value.replace('/s/', ' ')

                        # Handle access_log and error_log edge cases
                        if value == '':
                            continue  # skip log directives that are empty

                        if '$' in value and ' if=$' not in value:
                            continue  # skip directives that are use nginx variables and it's not if

                        # Otherwise handle normally (see ending else below).
                        indexed_value = self.__idx_save(value, file_index, row.line_number)
                        self.__simple_save(result, key, indexed_value)
                    elif key == 'ssl_certificate':
                        if value == '':
                            continue  # skip empty values

                        if '$' in value and ' if=$' not in value:
                            continue  # skip directives that are use nginx variables and it's not if

                        cert_path = self.resolve_local_path(value)
                        self.ssl_certificates.append(cert_path)  # Add value to ssl_certificates
                        self.populate_directories(cert_path)

                        # save config value
                        indexed_value = self.__idx_save(value, file_index, row.line_number)
                        self.__simple_save(result, key, indexed_value)
                    elif key == 'add_header':
                        indexed_value = self.__idx_save(value.replace('/s/', ' '), file_index, row.line_number)
                        self.__simple_save(result, key, indexed_value)
                    else:
                        indexed_value = self.__idx_save(value, file_index, row.line_number)
                        self.__simple_save(result, key, indexed_value)

        return result

    def __idx_save(self, value, file_index, line):
        new_index = len(self.index)

        # For performance, we should handle extra spaces in business logic instead of in pyparsing
        if isinstance(value, (str, unicode)):
            value = value.strip()
            value = value.replace('/s/', '')  # replace special spacers from __logic_parse() if they are still here

        self.index.append((file_index, line))
        return value, new_index

    def __simple_save(self, result, key, indexed_value):
        """
        We ended up having duplicate code when adding key-value pairs to our parsing dictionary (
        when handling access_log and error_log directives).

        This prompted us to refactor this process out to a separate function.  Because dictionaries are passed by
        reference in Python, we can alter the value dictionary in this local __func__ scope and have it affect the dict
        in the parent.

        :param result: dict Passed and altered by reference from the parent __func__ scope
        :param key:
        :param indexed_value:
        (No return since we are altering a pass-by-reference dict)
        """
        # simple key-value
        if key in result:
            stored_value = result[key]
            if isinstance(stored_value, list):
                result[key].append(indexed_value)
            else:
                result[key] = [stored_value, indexed_value]
        else:
            result[key] = indexed_value

    def simplify(self):
        """
        returns tree without index references
        can be used for debug/pretty output

        :return: dict of self.tree without index positions
        """
        def _simplify(tree):
            if isinstance(tree, dict):
                return dict((k, _simplify(v)) for k, v in tree.iteritems())
            elif isinstance(tree, list):
                return map(_simplify, tree)
            elif isinstance(tree, tuple):
                return _simplify(tree[0])
            return tree

        return _simplify(self.tree)

    def construct_directory_map(self):
        # start with directories
        for directory, info in self.directories.iteritems():
            self.directory_map[directory] = {'info': info, 'files': {}}

        for directory, error in izip(self.broken_directories, self.directory_errors):
            self.directory_map.setdefault(directory, {'info': {}, 'files': {}})
            self.directory_map[directory]['error'] = '%s: %s' % error

        # now files
        for filename, info in self.files.iteritems():
            directory = self.resolve_directory(filename)
            self.directory_map[directory]['files'][filename] = {'info': info}

        for filename, error in izip(self.broken_files, self.file_errors):
            directory = self.resolve_directory(filename)
            self.directory_map[directory]['files'].setdefault(filename, {'info': {}})
            self.directory_map[directory]['files'][filename]['error'] = '%s: %s' % error
