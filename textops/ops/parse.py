# -*- coding: utf-8 -*-
#
# Created : 2015-08-24
#
# @author: Eric Lapouyade
#
""" This module gathers parsers to handle whole input text"""

from textops import TextOp, NoAttr, dformat, pp
import textops
import string
import re
import copy
from datetime import datetime

logger = textops.logger

def index_normalize(index_val):
    """Normalize dictionary calculated key

    When parsing, keys within a dictionary may come from the input text. To ensure there is no
    space or other special caracters, one should use this function. This is useful because
    DictExt dictionaries can be access with a dotted notation that only supports ``A-Za-z0-9_`` chars.

    Args:
        index_val (str): The candidate string to a dictionary key.

    Returns:
        str: A normalized string with only ``A-Za-z0-9_`` chars

    Examples:
        >>> index_normalize('this my key')
        'this_my_key'
        >>> index_normalize('this -my- %key%')
        'this_my_key'

    """
    index_val = index_val.lower().strip()
    index_val = re.sub(r'^\W*','',index_val)
    index_val = re.sub(r'\W*$','',index_val)
    index_val = re.sub(r'\W+','_',index_val)
    index_val = re.sub('_+','_',index_val)
    return index_val

def context_key_not_found(key):
    return 'UNKNOWN_CONTEXT_KEY_%s' % key

class ParsingError(Exception):
    pass

class mgrep(TextOp):
    r"""Multiple grep

    This works like :class:`textops.grep` except that it can do several greps in a single command.
    By this way, you can select many patterns in a big file.

    Args:
        patterns_dict (dict): a dictionary where all patterns to search are in values.
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        dict: A dictionary where the keys are the same as for ``patterns_dict``, the values will
            contain the :class:`textops.grep` result for each corresponding patterns.

    Examples:
        >>> logs = '''
        ... error 1
        ... warning 1
        ... warning 2
        ... info 1
        ... error 2
        ... info 2
        ... '''
        >>> t = logs | mgrep({
        ... 'errors' : r'^err',
        ... 'warnings' : r'^warn',
        ... 'infos' : r'^info',
        ... })
        >>> print t                                         #doctest: +NORMALIZE_WHITESPACE
        {'infos': ['info 1', 'info 2'],
        'errors': ['error 1', 'error 2'],
        'warnings': ['warning 1', 'warning 2']}

        >>> s = '''
        ... Disk states
        ... -----------
        ... name: c1t0d0s0
        ... state: good
        ... fs: /
        ... name: c1t0d0s4
        ... state: failed
        ... fs: /home
        ...
        ... '''
        >>> t = s | mgrep({
        ... 'disks' : r'^name:',
        ... 'states' : r'^state:',
        ... 'fss' : r'^fs:',
        ... })
        >>> print t                                         #doctest: +NORMALIZE_WHITESPACE
        {'states': ['state: good', 'state: failed'],
        'disks': ['name: c1t0d0s0', 'name: c1t0d0s4'],
        'fss': ['fs: /', 'fs: /home']}
        >>> dict(zip(t.disks.cutre(': *',1),zip(t.states.cutre(': *',1),t.fss.cutre(': *',1))))
        {'c1t0d0s0': ('good', '/'), 'c1t0d0s4': ('failed', '/home')}
    """
    flags = 0
    reverse = False
    @classmethod
    def op(cls,text,patterns_dict,col_or_key = None, *args,**kwargs):
        for k,pattern in patterns_dict.items():
            if isinstance(pattern,basestring):
                patterns_dict[k] = re.compile(pattern,cls.flags)
        dct = {}
        for line in cls._tolist(text):
            for k,regex in patterns_dict.items():
                try:
                    if isinstance(line,basestring):
                        if bool(regex.search(line)) != cls.reverse:  # kind of XOR with cls.reverse
                            dct.setdefault(k,[]).append(line)
                    elif col_or_key is None:
                        if bool(regex.search(str(line))) != cls.reverse:  # kind of XOR with cls.reverse
                            dct.setdefault(k,[]).append(line)
                    else:
                        if bool(regex.search(line[col_or_key])) != cls.reverse:  # kind of XOR with cls.reverse
                            dct.setdefault(k,[]).append(line)
                except (ValueError, TypeError, IndexError, KeyError):
                    pass
        return dct

class mgrepi(mgrep):
    r"""same as mgrep but case insensitive

    This works like :class:`textops.mgrep`, except it is case insensitive.

    Args:
        patterns_dict (dict): a dictionary where all patterns to search are in values.
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        dict: A dictionary where the keys are the same as for ``patterns_dict``, the values will
            contain the :class:`textops.grepi` result for each corresponding patterns.

    Examples:
        >>> 'error 1' | mgrep({'errors':'ERROR'})
        {}
        >>> 'error 1' | mgrepi({'errors':'ERROR'})
        {'errors': ['error 1']}
    """
    flags = re.IGNORECASE

class mgrepv(mgrep):
    r"""Same as mgrep but exclusive

    This works like :class:`textops.mgrep`, except it searches lines that DOES NOT match patterns.

    Args:
        patterns_dict (dict): a dictionary where all patterns to exclude are in values().
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        dict: A dictionary where the keys are the same as for ``patterns_dict``, the values will
            contain the :class:`textops.grepv` result for each corresponding patterns.

    Examples:
        >>> logs = '''error 1
        ... warning 1
        ... warning 2
        ... error 2
        ... '''
        >>> t = logs | mgrepv({
        ... 'not_errors' : r'^err',
        ... 'not_warnings' : r'^warn',
        ... })
        >>> print t                                         #doctest: +NORMALIZE_WHITESPACE
        {'not_warnings': ['error 1', 'error 2'], 'not_errors': ['warning 1', 'warning 2']}
    """
    reverse = True

class mgrepvi(mgrepv):
    r"""Same as mgrepv but case insensitive

    This works like :class:`textops.mgrepv`, except it is case insensitive.

    Args:
        patterns_dict (dict): a dictionary where all patterns to exclude are in values().
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        dict: A dictionary where the keys are the same as for ``patterns_dict``, the values will
            contain the :class:`textops.grepvi` result for each corresponding patterns.

    Examples:
        >>> logs = '''error 1
        ... WARNING 1
        ... warning 2
        ... ERROR 2
        ... '''
        >>> t = logs | mgrepv({
        ... 'not_errors' : r'^err',
        ... 'not_warnings' : r'^warn',
        ... })
        >>> print t                                         #doctest: +NORMALIZE_WHITESPACE
        {'not_warnings': ['error 1', 'WARNING 1', 'ERROR 2'],
        'not_errors': ['WARNING 1', 'warning 2', 'ERROR 2']}
        >>> t = logs | mgrepvi({
        ... 'not_errors' : r'^err',
        ... 'not_warnings' : r'^warn',
        ... })
        >>> print t                                         #doctest: +NORMALIZE_WHITESPACE
        {'not_warnings': ['error 1', 'ERROR 2'], 'not_errors': ['WARNING 1', 'warning 2']}
    """
    flags = re.IGNORECASE

class parseg(TextOp):
    r"""Find all occurrences of one pattern, return MatchObject groupdict

    Args:
        pattern (str): a regular expression string (case sensitive)

    Returns:
        list: A list of dictionaries (MatchObject groupdict)

    Examples:
        >>> s = '''name: Lapouyade
        ... first name: Eric
        ... country: France'''
        >>> s | parseg(r'(?P<key>.*):\s*(?P<val>.*)')         #doctest: +NORMALIZE_WHITESPACE
        [{'key': 'name', 'val': 'Lapouyade'},
        {'key': 'first name', 'val': 'Eric'},
        {'key': 'country', 'val': 'France'}]
    """
    ignore_case = False
    @classmethod
    def op(cls,text, pattern, *args,**kwargs):
        if isinstance(pattern,basestring):
            pattern = re.compile(pattern, re.I if cls.ignore_case else 0)
        out = []
        for line in cls._tolist(text):
            m = pattern.match(line)
            if m:
                out.append(m.groupdict())
        return out

class parsegi(parseg):
    r"""Same as parseg but case insensitive

    Args:
        pattern (str): a regular expression string (case insensitive)

    Returns:
        list: A list of dictionaries (MatchObject groupdict)

    Examples:
        >>> s = '''Error: System will reboot
        ... Notice: textops rocks
        ... Warning: Python must be used without moderation'''
        >>> s | parsegi(r'(?P<level>error|warning):\s*(?P<msg>.*)')         #doctest: +NORMALIZE_WHITESPACE
        [{'msg': 'System will reboot', 'level': 'Error'},
        {'msg': 'Python must be used without moderation', 'level': 'Warning'}]
    """
    ignore_case = True

class parsek(TextOp):
    r"""Find all occurrences of one pattern, return one Key

    One have to give a pattern with named capturing parenthesis, the function will return a list
    of value corresponding to the specified key. It works a little like :class:`textops.parseg`
    except that it returns from the groupdict, a value for a specified key ('key' be default)

    Args:
        pattern (str): a regular expression string.
        key_name (str): The key to get ('key' by default)
        key_update (callable): function to convert the found value

    Returns:
        list: A list of values corrsponding to `MatchObject groupdict[key]`

    Examples:
        >>> s = '''Error: System will reboot
        ... Notice: textops rocks
        ... Warning: Python must be used without moderation'''
        >>> s | parsek(r'(?P<level>Error|Warning):\s*(?P<msg>.*)','msg')
        ['System will reboot', 'Python must be used without moderation']
    """
    ignore_case = False
    @classmethod
    def op(cls,text, pattern, key_name = 'key', key_update = None, *args,**kwargs):
        if isinstance(pattern,basestring):
            pattern = re.compile(pattern, re.I if cls.ignore_case else 0)
        out = []
        for line in cls._tolist(text):
            m = pattern.match(line)
            if m:
                dct = m.groupdict()
                key = dct.get(key_name)
                if key:
                    if key_update:
                        key = key_update(key)
                    out.append(key)
        return out

class parseki(parsek):
    r"""Same as parsek but case insensitive

    It works like :class:`textops.parsek` except the pattern is case insensitive.

    Args:
        pattern (str): a regular expression string.
        key_name (str): The key to get ('key' by default)
        key_update (callable): function to convert the found value

    Returns:
        list: A list of values corrsponding to `MatchObject groupdict[key]`

    Examples:
        >>> s = '''Error: System will reboot
        ... Notice: textops rocks
        ... Warning: Python must be used without moderation'''
        >>> s | parsek(r'(?P<level>error|warning):\s*(?P<msg>.*)','msg')
        []
        >>> s | parseki(r'(?P<level>error|warning):\s*(?P<msg>.*)','msg')
        ['System will reboot', 'Python must be used without moderation']
    """
    ignore_case = True

class parsekv(TextOp):
    r"""Find all occurrences of one pattern, returns a dict of groupdicts

    It works a little like :class:`textops.parseg` except that it returns a dict of dicts :
    values are MatchObject groupdicts, keys are a value in the groupdict at a specified key
    (By default : 'key'). Note that calculated keys are normalized (spaces are replaced by
    underscores)

    Args:
        pattern (str): a regular expression string.
        key_name (str): The key name to optain the value that will be the key of the groupdict
            ('key' by default)
        key_update (callable): function to convert/normalize the calculated key

    Returns:
        dict: A dict of MatchObject groupdicts

    Examples:
        >>> s = '''name: Lapouyade
        ... first name: Eric
        ... country: France'''
        >>> s | parsekv(r'(?P<key>.*):\s*(?P<val>.*)')         #doctest: +NORMALIZE_WHITESPACE
        {'country': {'val': 'France', 'key': 'country'},
        'first_name': {'val': 'Eric', 'key': 'first name'},
        'name': {'val': 'Lapouyade', 'key': 'name'}}
        >>> s | parsekv(r'(?P<item>.*):\s*(?P<val>.*)','item',str.upper)         #doctest: +NORMALIZE_WHITESPACE
        {'FIRST NAME': {'item': 'first name', 'val': 'Eric'},
        'NAME': {'item': 'name', 'val': 'Lapouyade'},
        'COUNTRY': {'item': 'country', 'val': 'France'}}
    """
    ignore_case = False
    @classmethod
    def op(cls,text, pattern, key_name = 'key', key_update = None, *args,**kwargs):
        if isinstance(pattern,basestring):
            pattern = re.compile(pattern, re.I if cls.ignore_case else 0)
        out = {}
        for line in cls._tolist(text):
            m = pattern.match(line)
            if m:
                dct = m.groupdict()
                key = dct.get(key_name)
                if key:
                    if key_update is None:
                        key_norm = index_normalize(key)
                    else:
                        key_norm = key_update(key)
                    out.update({ key_norm : dct })
        return out

class parsekvi(parsekv):
    r"""Find all occurrences of one pattern (case insensitive), returns a dict of groupdicts

    It works a little like :class:`textops.parsekv` except that the pattern is case insensitive.

    Args:
        pattern (str): a regular expression string (case insensitive).
        key_name (str): The key name to optain the value that will be the key of the groupdict
            ('key' by default)
        key_update (callable): function to convert/normalize the calculated key

    Returns:
        dict: A dict of MatchObject groupdicts

    Examples:
        >>> s = '''name: Lapouyade
        ... first name: Eric
        ... country: France'''
        >>> s | parsekvi(r'(?P<key>NAME):\s*(?P<val>.*)')
        {'name': {'val': 'Lapouyade', 'key': 'name'}}
    """
    ignore_case = True

class find_pattern(TextOp):
    r"""Fast pattern search

    This operation can be use to find a pattern very fast : it uses :func:`re.search` on the whole input
    text at once. The input text is not read line by line, this means it must fit into memory.
    It returns the first captured group (named or not named group).

    Args:
        pattern (str): a regular expression string (case sensitive).

    Returns:
        str: the first captured group or NoAttr if not found

    Examples:
        >>> s = '''This is data text
        ... Version: 1.2.3
        ... Format: json'''
        >>> s | find_pattern(r'^Version:\s*(.*)')
        '1.2.3'
        >>> s | find_pattern(r'^Format:\s*(?P<format>.*)')
        'json'
        >>> s | find_pattern(r'^version:\s*(.*)') # 'version' : no match because case sensitive
        NoAttr
    """
    ignore_case = False

    @classmethod
    def op(cls,text, pattern, *args,**kwargs):
        if isinstance(pattern,basestring):
            pattern = re.compile(pattern, re.M | (re.I if cls.ignore_case else 0))
        text = cls._tostr(text)
        m = pattern.search(text)
        if m :
            grps = m.groups()
            return grps[0] if grps else NoAttr
        return NoAttr

class find_patterni(find_pattern):
    r"""Fast pattern search (case insensitive)

    It works like :class:`textops.find_pattern` except that the pattern is case insensitive.

    Args:
        pattern (str): a regular expression string (case insensitive).

    Returns:
        str: the first captured group or NoAttr if not found

    Examples:
        >>> s = '''This is data text
        ... Version: 1.2.3
        ... Format: json'''
        >>> s | find_patterni(r'^version:\s*(.*)')
        '1.2.3'
    """
    ignore_case=True

class find_patterns(TextOp):
    r"""Fast multiple pattern search

    It works like :class:`textops.find_pattern` except that one can specify a list or a dictionary
    of patterns. Patterns must contains capture groups.
    It returns a list or a dictionary of results depending on the patterns argument type.
    Each result will be the re.MatchObject groupdict if there
    are more than one capture named group in the pattern otherwise directly the value corresponding
    to the unique captured group.
    It is recommended to use *named* capture group, if not, the groups will be automatically named
    'groupN' with N the capture group order in the pattern.

    Args:
        patterns (list or dict): a list or a dictionary of patterns.

    Returns:
        dict: patterns search result

    Examples:
        >>> s = '''This is data text
        ... Version: 1.2.3
        ... Format: json'''
        >>> r = s | find_patterns({
        ... 'version':r'^Version:\s*(?P<major>\d+)\.(?P<minor>\d+)\.(?P<build>\d+)',
        ... 'format':r'^Format:\s*(?P<format>.*)',
        ... })
        >>> r
        {'version': {'major': '1', 'build': '3', 'minor': '2'}, 'format': 'json'}
        >>> r.version.major
        '1'
        >>> s | find_patterns({
        ... 'version':r'^Version:\s*(\d+)\.(\d+)\.(\d+)',
        ... 'format':r'^Format:\s*(.*)',
        ... })
        {'version': {'group1': '2', 'group0': '1', 'group2': '3'}, 'format': 'json'}
        >>> s | find_patterns({'version':r'^version:\s*(.*)'}) # lowercase 'version' : no match
        {}
        >>> s = '''creation: 2015-10-14
        ... update: 2015-11-16
        ... access: 2015-11-17'''
        >>> s | find_patterns([r'^update:\s*(.*)', r'^access:\s*(.*)', r'^creation:\s*(.*)'])
        ['2015-11-16', '2015-11-17', '2015-10-14']
        >>> s | find_patterns([r'^update:\s*(?P<year>.*)-(?P<month>.*)-(?P<day>.*)',
        ... r'^access:\s*(.*)', r'^creation:\s*(.*)'])
        [{'month': '11', 'day': '16', 'year': '2015'}, '2015-11-17', '2015-10-14']
    """
    stop_when_found = False
    ignore_case = False

    @classmethod
    def op(cls,text, patterns,*args,**kwargs):
        out = []
        text = cls._tostr(text)
        if isinstance(patterns, dict):
            patterns_list = patterns.items()
        else:
            patterns_list = enumerate(patterns)
        for attr,pattern in patterns_list:
            if isinstance(pattern,basestring):
                pattern = re.compile(pattern, re.M | (re.I if cls.ignore_case else 0))
            if pattern:
                m = pattern.search(text)
                if m :
                    tmp_groupdict = m.groupdict() or dict([('group%s' % k,v) for k,v in enumerate(m.groups())])
                    groupdict = {}
                    for grp, val in tmp_groupdict.items():
                        if grp[:3] == 'INT':
                            try:
                                groupdict[grp[3:]] = int(val)
                            except ValueError:
                                groupdict[grp[3:]] = 0
                        else:
                            groupdict[grp] = val
                    groupdict = cls.pre_store(groupdict)
                    if len(groupdict) == 1:
                        out.append((attr, groupdict.popitem()[1]))
                    else:
                        out.append((attr, groupdict))
                    if cls.stop_when_found:
                        break
        if isinstance(patterns, dict):
            out = dict(out)
        else:
            out = [ i[1] for i in out ]
        return out

    @classmethod
    def pre_store(self,groupdict):
        return groupdict

class find_patternsi(find_patterns):
    r"""Fast multiple pattern search (case insensitive)

    It works like :class:`textops.find_patterns` except that patterns are case insensitive.

    Args:
        patterns (dict): a dictionary of patterns.

    Returns:
        dict: patterns search result

    Examples:
        >>> s = '''This is data text
        ... Version: 1.2.3
        ... Format: json'''
        >>> s | find_patternsi({'version':r'^version:\s*(.*)'})     # case insensitive
        {'version': '1.2.3'}
    """
    ignore_case=True


class find_first_pattern(find_patterns):
    r"""Fast multiple pattern search, returns on first match

    It works like :class:`textops.find_patterns` except that it stops searching on first match.

    Args:
        patterns (list): a list of patterns.

    Returns:
        str or dict: matched value if only one capture group otherwise the full groupdict

    Examples:
        >>> s = '''creation: 2015-10-14
        ... update: 2015-11-16
        ... access: 2015-11-17'''
        >>> s | find_first_pattern([r'^update:\s*(.*)', r'^access:\s*(.*)', r'^creation:\s*(.*)'])
        '2015-11-16'
        >>> s | find_first_pattern([r'^UPDATE:\s*(.*)'])
        NoAttr
        >>> s | find_first_pattern([r'^update:\s*(?P<year>.*)-(?P<month>.*)-(?P<day>.*)'])
        {'year': '2015', 'day': '16', 'month': '11'}
    """
    stop_when_found = True

    @classmethod
    def op(cls,text, patterns,*args,**kwargs):
        data = super(find_first_pattern,cls).op(text, patterns)
        if not data:
            return NoAttr
        return data[0]

class find_first_patterni(find_first_pattern):
    r"""Fast multiple pattern search, returns on first match

    It works like :class:`textops.find_first_pattern` except that patterns are case insensitives.

    Args:
        patterns (list): a list of patterns.

    Returns:
        str or dict: matched value if only one capture group otherwise the full groupdict

    Examples:
        >>> s = '''creation: 2015-10-14
        ... update: 2015-11-16
        ... access: 2015-11-17'''
        >>> s | find_first_patterni([r'^UPDATE:\s*(.*)'])
        '2015-11-16'
    """
    ignore_case=True

class parse_indented(TextOp):
    r"""Parse key:value indented text

    It looks for key:value patterns, store found values in a dictionary. Each time a new indent is
    found, a sub-dictionary is created. The keys are normalized (only keep ``A-Za-z0-9_``), the values
    are stripped.

    Args:
        sep (str): key:value separator (Default : ':')

    Returns:
        dict: structured keys:values

    Examples:
        >>> s = '''
        ... a:val1
        ... b:
        ...     c:val3
        ...     d:
        ...         e ... : val5
        ...         f ... :val6
        ...     g:val7
        ... f: val8'''
        >>> s | parse_indented()
        {'a': 'val1', 'b': {'c': 'val3', 'd': {'e': 'val5', 'f': 'val6'}, 'g': 'val7'}, 'f': 'val8'}
        >>> s = '''
        ... a --> val1
        ... b --> val2'''
        >>> s | parse_indented(r'-->')
        {'a': 'val1', 'b': 'val2'}
    """
    @classmethod
    def op(cls, text, sep=r':', *args,**kwargs):
        indent_level = 0
        out = {}
        indent_node = {indent_level:out}
        dct = out
        prev_k = None
        # parse the text
        for line in cls._tolist(text):
            m = re.match(r'^(\s*)(\S.*)', line)
            if m:
                k,v = (re.split(sep,m.group(2)) + [''])[:2]
                indent = len(m.group(1))
                if indent < indent_level:
                    dct = indent_node.get(indent)
                    while dct is None:
                        indent -= 1
                        dct = indent_node.get(indent)
                    indent_level = indent
                    for ik in indent_node.keys():
                        if ik > indent:
                            del indent_node[ik]
                elif indent > indent_level:
                    if prev_k is not None:
                        dct[prev_k] = {}
                        dct = dct[prev_k]
                    indent_node[indent] = dct
                    indent_level = indent
                k = index_normalize(k)
                v = v.strip()
                if k in dct:
                    prev_v = dct[k]
                    if isinstance(prev_v,dict):
                        dct[k]=[prev_v,{}]
                        dct = dct[k][-1]
                    elif isinstance(prev_v,basestring):
                        dct[k]=[prev_v,v]
                    else:
                        if isinstance(prev_v[0],basestring):
                            dct[k].append(v)
                        else:
                            dct[k].append({})
                            dct = dct[k][-1]
                    prev_k = None
                else:
                    dct[k]=v
                    prev_k = k
        return out

class state_pattern(TextOp):
    r""" States and patterns parser

    This is a *state machine* parser : 
    The main advantage is that it reads line-by-line the whole input text only once to collect all
    data you want into a multi-level dictionary. It uses patterns to select rules to be applied.
    It uses states to ensure only a set of rules are used against specific document sections. 

    Args:
        states_patterns_desc (tupple) : descrption of states and patterns :
            see below for explaination
        reflags : re flags, ie re.I or re.M or re.I | re.M (Default : no flag)
        autostrip : before being stored, groupdict keys and values are stripped (Default : True)

    Returns:
        dict : parsed data from text

    |
    | **The states_patterns_desc :**

    It looks like this::

        ((<if state1>,<goto state1>,<pattern1>,<out data path1>,<out filter1>),
        ...
        (<if stateN>,<goto stateN>,<patternN>,<out data pathN>,<out filterN>))

    ``<if state>``
        is a string telling on what state(s) the pattern must be searched,
        one can specify several states with comma separated string or a tupple. if ``<if state>``
        is empty, the pattern will be searched for all lines.
        Note : at the beginning, the state is 'top'

    ``<goto state>``
        is a string corresponding to the new state if the pattern matches.
        use an empty string to not change the current state. One can use any string, usually,
        it corresponds to a specific section name of the document to parse where specific
        rules has to be used.

    ``<pattern>``
        is a string or a re.regex to match a line of text.
        one should use named groups for selecting data, ex: ``(?P<key1>pattern)``

    ``<out data path>``
        is a string with a dot separator or a tuple telling where to place the groupdict
        from pattern maching process,
        The syntax is::

            '{contextkey1}.{contextkey2}. ... .{contextkeyN}'
            or
            ('{contextkey1}','{contextkey2}', ... ,'{contextkeyN}')
            or
            'key1.key2.keyN'
            or
            'key1.key2.keyN[]'
            or
            '{contextkey1}.{contextkey2}. ... .keyN[]'

        The contextdict is used to format strings with ``{contextkeyN}`` syntax.
        instead of ``{contextkeyN}``, one can use a simple string to put data in a fixed path.
        Once the path fully formatted, let's say to ``key1.key2.keyN``, the parser will store the
        value into the result dictionnary at :
        ``{'key1':{'key2':{'keyN' : thevalue }}}``
        One can use the string ``[]`` at the end of the path : the groupdict will be appended in a list
        ie : ``{'key1':{'key2':{'keyN' : [thevalue,...] }}}``

    ``<out filter>``
        is used to build the value to store,

        it could be :

            * None : no filter is applied, the re.MatchObject.groupdict() is stored
            * a string : used as a format string with context dict, the formatted string is stored
            * a callable : to calculate the value to be stored, the context dict is given as param.

    **How the parser works :**

    You have a document where the syntax may change from one section to an another : You have just
    to give a name to these kind of sections : it will be your state names.
    The parser reads line by line the input text : For each line, it will look for the *first*
    matching rule from ``states_patterns_desc`` table, then will apply the rule.
    One rule has got 2 parts : the matching parameters, and the action parameters.

    Matching parameters:
        To match, a rule requires the parser to be at the specified state ``<if state>`` AND
        the line to be parsed must match the pattern ``<pattern>``. When the parser is at the first
        line, it has the default state ``top``. The pattern follow the
        standard python ``re`` module syntax. It is important to note that you must capture text
        you want to collect with the named group capture syntax, that is ``(?P<mydata>mypattern)``.
        By this way, the parser will store text corresponding to ``mypattern`` to a contextdict at
        the key ``mydata``.

    Action parameters:
        Once the rule matches, the action is to store ``<out filter>`` into the final dictionary at
        a specified ``<out data path>``.

    **Context dict :**

    The context dict is used within ``<out filter>`` and ``<out data path>``, it is a dictionary that
    is *PERSISTENT* during the whole parsing process :
    It is empty at the parsing beginning and will accumulate all captured pattern. For exemple, if
    a first rule pattern contains ``(?P<key1>.*),(?P<key2>.*)`` and matches the document line
    ``val1,val2``, the context dict will be ``{ 'key1' : 'val1', 'key2' : 'val2' }``. Then if a
    second rule pattern contains ``(?P<key2>.*):(?P<key3>.*)`` and matches the document line
    ``val4:val5`` then the context dict will be *UPDATED* to
    ``{ 'key1' : 'val1', 'key2' : 'val4', 'key3' : 'val5' }``.
    As you can see, the choice of the key names are *VERY IMPORTANT* in order to avoid collision
    across all the rules.

    Examples:

        >>> s = '''
        ... first name: Eric
        ... last name: Lapouyade'''
        >>> s | state_pattern( (('',None,'(?P<key>.*):(?P<val>.*)','{key}','{val}'),) )
        {'first_name': 'Eric', 'last_name': 'Lapouyade'}
        >>> s | state_pattern( (('',None,'(?P<key>.*):(?P<val>.*)','{key}',None),) ) #doctest: +NORMALIZE_WHITESPACE
        {'first_name': {'val': 'Eric', 'key': 'first name'},
        'last_name': {'val': 'Lapouyade', 'key': 'last name'}}
        >>> s | state_pattern((('',None,'(?P<key>.*):(?P<val>.*)','my.path.{key}','{val}'),))
        {'my': {'path': {'first_name': 'Eric', 'last_name': 'Lapouyade'}}}

        >>> s = '''Eric
        ... Guido'''
        >>> s | state_pattern( (('',None,'(?P<val>.*)','my.path.info[]','{val}'),) )
        {'my': {'path': {'info': ['Eric', 'Guido']}}}

        >>> s = '''
        ... Section 1
        ... ---------
        ...   email = ericdupo@gmail.com
        ...
        ... Section 2
        ... ---------
        ...   first name: Eric
        ...   last name: Dupont'''
        >>> s | state_pattern( (                                    #doctest: +NORMALIZE_WHITESPACE
        ... ('','section1','^Section 1',None,None),
        ... ('','section2','^Section 2',None,None),
        ... ('section1', '', '(?P<key>.*)=(?P<val>.*)', 'section1.{key}', '{val}'),
        ... ('section2', '', '(?P<key>.*):(?P<val>.*)', 'section2.{key}', '{val}')) )
        {'section2': {'first_name': 'Eric', 'last_name': 'Dupont'},
        'section1': {'email': 'ericdupo@gmail.com'}}

        >>> s = '''
        ... Disk states
        ... -----------
        ... name: c1t0d0s0
        ... state: good
        ... fs: /
        ... name: c1t0d0s4
        ... state: failed
        ... fs: /home
        ...
        ... '''
        >>> s | state_pattern( (                                    #doctest: +NORMALIZE_WHITESPACE
        ... ('top','disk',r'^Disk states',None,None),
        ... ('disk','top', r'^\s*$',None,None),
        ... ('disk', '', r'^name:(?P<diskname>.*)',None, None),
        ... ('disk', '', r'(?P<key>.*):(?P<val>.*)', 'disks.{diskname}.{key}', '{val}')) )
        {'disks': {'c1t0d0s0': {'state': 'good', 'fs': '/'},
        'c1t0d0s4': {'state': 'failed', 'fs': '/home'}}}

    """

    @classmethod
    def op(cls,text, states_patterns_desc, reflags=0, autostrip=True,**kwargs):
        state = 'top'
        root_data = {}
        groups_context = {}
        states_patterns = []

        #check states_patterns_desc is a correct tuple/list of tuples/lists
        if not isinstance(states_patterns_desc,(list,tuple)):
            raise ParsingError('states_patterns_desc must contains a tuple/list of tuples/lists')
        if not states_patterns_desc or not states_patterns_desc[0]:
            raise ParsingError('states_patterns_desc must not be empty')
        if not isinstance(states_patterns_desc[0],(list,tuple)):
            raise ParsingError('states_patterns_desc must contains a tuple/list of tuples/lists : one level of parenthesis or a coma is missing somewhere.')
        if len(states_patterns_desc[0]) != 5:
            raise ParsingError('states_patterns_desc subtuple must contain 5 elements : ifstate, gotostate, pattern, datapath and outfilter')

        #normalizing states_patterns_desc :
        for ifstate, gotostate, pattern, datapath, outfilter in states_patterns_desc:
            if not ifstate:
                ifstate = ()
            else:
                if isinstance(ifstate, basestring):
                    ifstate = ifstate.split(',')
            if isinstance(pattern, basestring):
                pattern = re.compile(pattern,reflags)
            if isinstance(datapath, basestring):
                if not datapath:
                    datapath = []
                else:
                    datapath = datapath.split('.')
            states_patterns.append((ifstate, gotostate, pattern, datapath, outfilter))

        # parse the text
        for line in cls._tolist(text):
            logger.debug('state:%10s, line = %s',state, line)
            for ifstate, gotostate, pattern, datapath, outfilter in states_patterns:
                logger.debug('  ? %10s "%10s" r\'%s\' "%s" "%s"',ifstate, gotostate, pattern.pattern, datapath, outfilter)
                if not ifstate or state in ifstate:
                    m=pattern.match(line)
                    if m:
                        g = m.groupdict()
                        if autostrip:
                            g = dict([ (k,v.strip()) for k,v in m.groupdict().items() ])
                        groups_context.update(g)
                        logger.debug('  -> OK')
                        logger.debug('    context = %s',groups_context)
                        if datapath is not None:
                            data = root_data
                            for p in datapath:
                                p = dformat(p,groups_context,context_key_not_found)
                                prev_data = data
                                if p[-2:] == '[]':
                                    p = p[:-2]
                                    p = index_normalize(p)
                                    if p not in data:
                                        data[p] = []
                                    data = data[p]
                                else:
                                    p = index_normalize(p)
                                    if p not in data:
                                        data[p] = {}
                                    data = data[p]

                            if callable(outfilter):
                                g=outfilter(g)
                            elif isinstance(outfilter, basestring):
                                g=dformat(outfilter,groups_context,context_key_not_found)

                            if isinstance(data,list):
                                data.append(g)
                            else:
                                if isinstance(g,dict):
                                    data.update(g)
                                else:
                                    prev_data[p] = g
                        if gotostate:
                            state = gotostate
                        break
        return root_data
