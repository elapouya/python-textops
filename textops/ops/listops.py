# -*- coding: utf-8 -*-
#
# Created : 2015-04-03
#
# @author: Eric Lapouyade
#
""" This module gathers list/line operations """

from textops import TextOp, dformat
import re
import subprocess
import sys
import os
import itertools

class ListOpError(Exception):
    pass

class cat(TextOp):
    r""" Return the content of the file with the path given in the input text

    If a context dict is specified, the path is formatted with that context (str.format)

    Args:
        context (dict): The context to format the file path (Optionnal)

    Yields:
        str: the file content lines

    Examples:
        >>> open('/tmp/testfile.txt','w').write('here is the file content')
        >>> '/tmp/testfile.txt' | cat()                 #doctest: +ELLIPSIS
        <generator object extend_type_gen at ...>
        >>> '/tmp/testfile.txt' | cat().tostr()
        'here is the file content'
        >>> '/tmp/testfile.txt' >> cat()
        ['here is the file content']
        >>> '/tmp/testfile.txt' | cat().upper().tostr()
        'HERE IS THE FILE CONTENT'
        >>> context = {'path':'/tmp/'}
        >>> '{path}testfile.txt' | cat(context)                 #doctest: +ELLIPSIS
        <generator object extend_type_gen at ...>
        >>> '{path}testfile.txt' | cat(context).tostr()
        'here is the file content'
        >>> cat('/tmp/testfile.txt').s
        'here is the file content'
        >>> cat('/tmp/testfile.txt').upper().s
        'HERE IS THE FILE CONTENT'
        >>> cat('/tmp/testfile.txt').l
        ['here is the file content']
        >>> cat('/tmp/testfile.txt').g                 #doctest: +ELLIPSIS
        <generator object extend_type_gen at ...>
        >>> for line in cat('/tmp/testfile.txt'):
        ...     print line
        ...
        here is the file content
        >>> for bits in cat('/tmp/testfile.txt').grep('content').cut():
        ...     print bits
        ...
        ['here', 'is', 'the', 'file', 'content']
        >>> open('/tmp/testfile.txt','w').write('here is the file content\nanother line')
        >>> '/tmp/testfile.txt' | cat().tostr()
        'here is the file content\nanother line'
        >>> '/tmp/testfile.txt' | cat().tolist()
        ['here is the file content', 'another line']
        >>> cat('/tmp/testfile.txt').s
        'here is the file content\nanother line'
        >>> cat('/tmp/testfile.txt').l
        ['here is the file content', 'another line']
        >>> context = {'path': '/tmp/'}
        >>> cat('/{path}/testfile.txt',context).l
        ['here is the file content', 'another line']
        >>> for bits in cat('/tmp/testfile.txt').grep('content').cut():
        ...     print bits
        ...
        ['here', 'is', 'the', 'file', 'content']
    """
    @classmethod
    def op(cls,text, context = {},*args,**kwargs):
        for path in cls._tolist(text):
            if context:
                path = path.format(**context)
            if os.path.isfile(path) or os.path.islink(path):
                with open(path) as fh:
                    for line in fh:
                        yield line.rstrip('\r\n')

class run(TextOp):
    r""" Run the command from the input text and return execution output

    | This text operation use subprocess.Popen to call the command.
    | If the command is a string, it will be executed within a shell.
    | If the command is a list (the command and its arguments), the command is executed without a shell.
    | If a context dict is specified, the command is formatted with that context (str.format)

    Args:
        context (dict): The context to format the command to run

    Yields:
        str: the execution output

    Examples:
        >>> cmd = 'mkdir -p /tmp/textops_tests_run;\
        ... cd /tmp/textops_tests_run; touch f1 f2 f3; ls'
        >>> print cmd | run().tostr()
        f1
        f2
        f3
        >>> print cmd >> run()
        ['f1', 'f2', 'f3']
        >>> print ['ls', '/tmp/textops_tests_run'] | run().tostr()
        f1
        f2
        f3
        >>> print ['ls', '{path}'] | run({'path':'/tmp/textops_tests_run'}).tostr()
        f1
        f2
        f3
    """
    @classmethod
    def op(cls,text, context = {},*args,**kwargs):
        if isinstance(text, basestring):
            if context:
                text = text.format(**context)
            p=subprocess.Popen(['sh','-c',text],stdout=subprocess.PIPE)
        else:
            if context:
                text = [ t.format(**context) for t in text ]
            p=subprocess.Popen(text,stdout=subprocess.PIPE)
        while p.returncode is None:
            (stdout, stderr) = p.communicate()
            for line in stdout.splitlines():
                yield line

class mrun(TextOp):
    r""" Run multiple commands from the input text and return execution output

    | This works like :class:`textops.run` except that each line of the input text will be used as a command.
    | The input text must be a list of strings (list, generator, or newline separated), \
      not a list of lists. Commands will be executed inside a shell.
    | If a context dict is specified, commands are formatted with that context (str.format)

    Args:
        context (dict): The context to format the command to run

    Yields:
        str: the execution output

    Examples:
        >>> cmds = 'mkdir -p /tmp/textops_tests_run\n'
        >>> cmds+= 'cd /tmp/textops_tests_run;touch f1 f2 f3\n'
        >>> cmds+= 'ls /tmp/textops_tests_run'
        >>> print cmds | mrun().tostr()
        f1
        f2
        f3
        >>> cmds=['mkdir -p /tmp/textops_tests_run',
        ... 'cd /tmp/textops_tests_run; touch f1 f2 f3']
        >>> cmds.append('ls /tmp/textops_tests_run')
        >>> print cmds | mrun().tostr()
        f1
        f2
        f3
        >>> print cmds >> mrun()
        ['f1', 'f2', 'f3']
        >>> cmds = ['ls {path}', 'echo "Cool !"']
        >>> print cmds | mrun({'path':'/tmp/textops_tests_run'}).tostr()
        f1
        f2
        f3
        Cool !
    """
    @classmethod
    def op(cls,text, context = {}, *args,**kwargs):
        for cmd in cls._tolist(text):
            if context:
                cmd = cmd.format(**context)
            p=subprocess.Popen(['sh','-c',cmd],stdout=subprocess.PIPE)
            while p.returncode is None:
                (stdout, stderr) = p.communicate()
                for line in stdout.splitlines():
                    yield line

class grep(TextOp):
    r"""Select lines having a specified pattern

    This works like the shell command 'egrep' : it will filter the input text and retain only
    lines matching the pattern.

    It works for any kind of list of strings, but also for list of lists and list of dicts.
    In these cases, one can test only one column or one key but return the whole list/dict.
    before testing, the object to be tested is converted into a string with str() so the grep
    will work for any kind of object.

    Args:
        pattern (str): a regular expression string (case sensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str, list or dict: the filtered input text

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grep('error')  #doctest: +ELLIPSIS
        <generator object extend_type_gen at ...>
        >>> input | grep('error').tolist()
        ['error1', 'error2']
        >>> input >> grep('error')
        ['error1', 'error2']
        >>> input | grep('ERROR').tolist()
        []
        >>> input | grep('error|warning').tolist()
        ['error1', 'error2', 'warning1', 'warning2']
        >>> input | cutca(r'(\D+)(\d+)')                         #doctest: +NORMALIZE_WHITESPACE
        [('error', '1'), ('error', '2'), ('warning', '1'),
        ('info', '1'), ('warning', '2'), ('info', '2')]
        >>> input | cutca(r'(\D+)(\d+)').grep('1',1).tolist()
        [('error', '1'), ('warning', '1'), ('info', '1')]
        >>> input | cutdct(r'(?P<level>\D+)(?P<nb>\d+)') #doctest: +NORMALIZE_WHITESPACE
        [{'nb': '1', 'level': 'error'}, {'nb': '2', 'level': 'error'},
        {'nb': '1', 'level': 'warning'}, {'nb': '1', 'level': 'info'},
        {'nb': '2', 'level': 'warning'}, {'nb': '2', 'level': 'info'}]
        >>> input | cutdct(r'(?P<level>\D+)(?P<nb>\d+)').grep('1','nb').tolist() #doctest: +NORMALIZE_WHITESPACE
        [{'nb': '1', 'level': 'error'}, {'nb': '1', 'level': 'warning'},
        {'nb': '1', 'level': 'info'}]
        >>> [{'more simple':1},{'way to grep':2},{'list of dicts':3}] | grep('way').tolist()
        [{'way to grep': 2}]
        >>> [{'more simple':1},{'way to grep':2},{'list of dicts':3}] | grep('3').tolist()
        [{'list of dicts': 3}]

    """
    flags = 0
    reverse = False
    pattern = ''
    @classmethod
    def op(cls,text,pattern=None,col_or_key = None, *args,**kwargs):
        if pattern is None:
            pattern = cls.pattern
        regex = re.compile(pattern,cls.flags)
        for line in cls._tolist(text):
            try:
                if isinstance(line,basestring):
                    if bool(regex.search(line)) != cls.reverse:  # kind of XOR with cls.reverse
                        yield line
                elif col_or_key is None:
                    if bool(regex.search(str(line))) != cls.reverse:  # kind of XOR with cls.reverse
                        yield line
                else:
                    if bool(regex.search(str(line[col_or_key]))) != cls.reverse:  # kind of XOR with cls.reverse
                        yield line
            except (ValueError, TypeError, IndexError, KeyError):
                pass

class grepi(grep):
    r"""grep case insensitive

    This works like :class:`textops.grep`, except it is case insensitive.

    Args:
        pattern (str): a regular expression string (case insensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str, list or dict: the filtered input text

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepi('ERROR').tolist()
        ['error1', 'error2']
        >>> input >> grepi('ERROR')
        ['error1', 'error2']
    """
    flags = re.IGNORECASE

class grepv(grep):
    r"""grep with inverted matching

    This works like :class:`textops.grep`, except it returns lines that does NOT match the specified pattern.

    Args:
        pattern (str): a regular expression string
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str, list or dict: the filtered input text

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepv('error').tolist()
        ['warning1', 'info1', 'warning2', 'info2']
        >>> input >> grepv('error')
        ['warning1', 'info1', 'warning2', 'info2']
        >>> input | grepv('ERROR').tolist()
        ['error1', 'error2', 'warning1', 'info1', 'warning2', 'info2']
    """
    reverse = True

class grepvi(grepv):
    r"""grep case insensitive with inverted matching

    This works like :class:`textops.grepv`, except it is case insensitive.

    Args:
        pattern (str): a regular expression string (case insensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str, list or dict: the filtered input text

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepvi('ERROR').tolist()
        ['warning1', 'info1', 'warning2', 'info2']
        >>> input >> grepvi('ERROR')
        ['warning1', 'info1', 'warning2', 'info2']
    """
    flags = re.IGNORECASE

class grepc(TextOp):
    r"""Count lines having a specified pattern

    This works like :class:`textops.grep` except that instead of filtering the input text,
    it counts lines matching the pattern.

    Args:
        pattern (str): a regular expression string (case sensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        int: the matched lines count

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepc('error')
        2
        >>> input | grepc('ERROR')
        0
        >>> input | grepc('error|warning')
        4
        >>> [{'more simple':1},{'way to grep':2},{'list of dicts':3}] | grepc('3')
        1
        >>> [{'more simple':1},{'way to grep':2},{'list of dicts':3}] | grepc('2','way to grep')
        1

    """
    flags = 0
    reverse = False
    pattern = ''
    exit_on_found = False
    @classmethod
    def op(cls,text,pattern=None,col_or_key = None,*args,**kwargs):
        if text is None:
            return 0
        if pattern is None:
            pattern = cls.pattern
        regex = re.compile(pattern,cls.flags)
        count = 0
        for line in cls._tolist(text):
            try:
                if isinstance(line,basestring):
                    if bool(regex.search(line)) != cls.reverse:  # kind of XOR with cls.reverse
                        count += 1
                        if cls.exit_on_found:
                            break
                elif col_or_key is None:
                    if bool(regex.search(str(line))) != cls.reverse:  # kind of XOR with cls.reverse
                        count += 1
                        if cls.exit_on_found:
                            break
                else:
                    if bool(regex.search(str(line[col_or_key]))) != cls.reverse:  # kind of XOR with cls.reverse
                        count += 1
                        if cls.exit_on_found:
                            break
            except (ValueError, TypeError, IndexError, KeyError):
                pass
        if cls.exit_on_found:
            return bool(count)
        return count

class grepci(grepc):
    r"""Count lines having a specified pattern (case insensitive)

    This works like :class:`textops.grepc` except that the pattern is case insensitive

    Args:
        pattern (str): a regular expression string (case insensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        int: the matched lines count

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepci('ERROR')
        2
    """
    flags = re.IGNORECASE

class grepcv(grepc):
    r"""Count lines NOT having a specified pattern

    This works like :class:`textops.grepc` except that it counts line that does NOT match the pattern.

    Args:
        pattern (str): a regular expression string (case sensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        int: the NOT matched lines count

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepcv('error')
        4
        >>> input | grepcv('ERROR')
        6
    """
    reverse = True

class grepcvi(grepcv):
    r"""Count lines NOT having a specified pattern (case insensitive)

    This works like :class:`textops.grepcv` except that the pattern is case insensitive

    Args:
        pattern (str): a regular expression string (case insensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        int: the NOT matched lines count

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | grepcvi('ERROR')
        4
    """
    flags = re.IGNORECASE

class haspattern(grepc):
    r"""Tests if the input text matches the specified pattern

    This reads the input text line by line (or item by item for lists and generators), cast into
    a string before testing. like :class:`textops.grepc` it accepts testing on a specific column
    for a list of lists or testing on a specific key for list of dicts.
    It stops reading the input text as soon as the pattern is found : it is useful for big input text.

    Args:
        pattern (str): a regular expression string (case sensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        bool: True if the pattern is found.

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | haspattern('error')
        True
        >>> input | haspattern('ERROR')
        False
    """
    exit_on_found = True

class haspatterni(haspattern):
    r"""Tests if the input text matches the specified pattern

    Works like :class:`textops.haspattern` except that it is case insensitive.

    Args:
        pattern (str): a regular expression string (case insensitive)
        col_or_key (int or str): test only one column or one key (optional)

    Returns:
        bool: True if the pattern is found.

    Examples:
        >>> input = 'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input | haspatterni('ERROR')
        True
    """
    flags = re.IGNORECASE

class rmblank(grepv):
    r"""Remove any kind of blank lines from the input text

    A blank line can be an empty line or a line with only spaces and/or tabs.

    Returns:
        generator: input text without blank lines

    Examples:
        >>> input = 'error1\n\n\nerror2\nwarning1\n   \t \t \ninfo1\nwarning2\ninfo2'
        >>> input | rmblank().tostr()
        'error1\nerror2\nwarning1\ninfo1\nwarning2\ninfo2'
        >>> input = ['a','','b','   ','c','  \t\t','d']
        >>> input | rmblank().tolist()
        ['a', 'b', 'c', 'd']
    """
    pattern = r'^\s*$'

class formatitems(TextOp):
    r"""Formats list of 2-sized tuples

    Useful to convert list of 2-sized tuples into a simple string
    It converts the list of tuple into a list of strings by using the ``format_str``, then it
    joins all the strings with ``join_str`` to get a unique simple string.

    Args:
        format_str(str): format string, default is '{0} : {1}\n'
        join_str(str): string to join all strings into one unique string, default is ''

    Returns:
        str: formatted input

    Examples:
        >>> [('key1','val1'),('key2','val2')] | formatitems('{0} -> {1}\n')
        'key1 -> val1\nkey2 -> val2\n'
        >>> [('key1','val1'),('key2','val2')] | formatitems('{0}:{1}',', ')
        'key1:val1, key2:val2'
    """
    @classmethod
    def op(cls,items,format_str='{0} : {1}\n',join_str = '', *args,**kwargs):
        return join_str.join([format_str.format(k,v) for k,v in items ])

class formatlists(TextOp):
    r"""Formats list of lists

    Useful to convert list of lists into a simple string
    It converts the list of lists into a list of strings by using the ``format_str``, then it
    joins all the strings with ``join_str`` to get a unique simple string.

    Args:
        format_str(str): format string, default is '{0} : {1}\n'
        join_str(str): string to join all strings into one unique string, default is ''

    Returns:
        str: formatted input

    Examples:
        >>> [['key1','val1','help1'],['key2','val2','help2']] | formatlists('{2} : {0} -> {1}\n')
        'help1 : key1 -> val1\nhelp2 : key2 -> val2\n'
        >>> [['key1','val1','help1'],['key2','val2','help2']] | formatlists('{0}:{1} ({2})',', ')
        'key1:val1 (help1), key2:val2 (help2)'
    """
    @classmethod
    def op(cls,items,format_str='{0} : {1}\n',join_str = '', *args,**kwargs):
        return join_str.join([format_str.format(*lst) for lst in items ])

class formatdicts(TextOp):
    r"""Formats list of dicts

    Useful to convert list of dicts into a simple string.
    It converts the list of dicts into a list of strings by using the ``format_str``, then it
    joins all the strings with ``join_str`` to get a unique simple string.

    Args:
        format_str(str): format string, default is '{key} : {val}\n'
        join_str(str): string to join all strings into one unique string, default is ''
        defvalue(str): The replacement string or function for unexisting keys when formating.

    Returns:
        str: formatted input

    Examples:
        >>> input = [{'key':'a','val':1},{'key':'b','val':2},{'key':'c'}]
        >>> input | formatdicts()
        'a : 1\nb : 2\nc : -\n'
        >>> input | formatdicts('{key} -> {val}\n',defvalue='N/A')
        'a -> 1\nb -> 2\nc -> N/A\n'
        >>> input = [{'name':'Eric','age':47,'level':'guru'},
        ... {'name':'Guido','age':59,'level':'god'}]
        >>> print input | formatdicts('{name}({age}) : {level}\n')   #doctest: +NORMALIZE_WHITESPACE
        Eric(47) : guru
        Guido(59) : god
        >>> print input | formatdicts('{name}', ', ')
        Eric, Guido
    """
    @classmethod
    def op(cls,items,format_str='{key} : {val}\n',join_str = '',defvalue='-',*args,**kwargs):
        return join_str.join([dformat(format_str,dct,defvalue) for dct in items ])

class first(TextOp):
    r"""Return the first line/item from the input text

    Returns:
        StrExt, ListExt or DictExt: the first line/item from the input text

    Examples:
        >>> 'a\nb\nc' | first()
        'a'
        >>> ['a','b','c'] | first()
        'a'
        >>> [('a',1),('b',2),('c',3)] | first()
        ['a', 1]
        >>> [['key1','val1','help1'],['key2','val2','help2']] | first()
        ['key1', 'val1', 'help1']
        >>> [{'key':'a','val':1},{'key':'b','val':2},{'key':'c','val':3}] | first()
        {'key': 'a', 'val': 1}
    """
    @classmethod
    def op(cls,text,*args,**kwargs):
        for line in cls._tolist(text):
            return line
        return ''

class last(TextOp):
    r"""Return the last line/item from the input text

    Returns:
        StrExt, ListExt or DictExt: the last line/item from the input text

    Examples:
        >>> 'a\nb\nc' | last()
        'c'
        >>> ['a','b','c'] | last()
        'c'
        >>> [('a',1),('b',2),('c',3)] | last()
        ['c', 3]
        >>> [['key1','val1','help1'],['key2','val2','help2']] | last()
        ['key2', 'val2', 'help2']
        >>> [{'key':'a','val':1},{'key':'b','val':2},{'key':'c','val':3}] | last()
        {'key': 'c', 'val': 3}
    """
    @classmethod
    def op(cls,text,*args,**kwargs):
        last = ''
        for line in cls._tolist(text):
            last = line
        return last

class head(TextOp):
    r"""Return first lines from the input text

    Args:
        lines(int): The number of lines/items to return.

    Yields:
        str, lists or dicts: the first 'lines' lines from the input text

    Examples:
        >>> 'a\nb\nc' | head(2).tostr()
        'a\nb'
        >>> for l in 'a\nb\nc' | head(2):
        ...   print l
        a
        b
        >>> ['a','b','c'] | head(2).tolist()
        ['a', 'b']
        >>> ['a','b','c'] >> head(2)
        ['a', 'b']
        >>> [('a',1),('b',2),('c',3)] | head(2).tolist()
        [('a', 1), ('b', 2)]
        >>> [{'key':'a','val':1},{'key':'b','val':2},{'key':'c','val':3}] | head(2).tolist()
        [{'val': 1, 'key': 'a'}, {'val': 2, 'key': 'b'}]
    """
    @classmethod
    def op(cls,text,lines,*args,**kwargs):
        for i,line in enumerate(cls._tolist(text)):
            if i >= lines:
                break
            yield line

class skip(TextOp):
    r"""Skip n lines

    It will return the input text except the n first lines

    Args:
        lines(int): The number of lines/items to skip.

    Yields:
        str, lists or dicts: skip 'lines' lines from the input text

    Examples:
        >>> 'a\nb\nc' | skip(1).tostr()
        'b\nc'
        >>> for l in 'a\nb\nc' | skip(1):
        ...   print l
        b
        c
        >>> ['a','b','c'] | skip(1).tolist()
        ['b', 'c']
        >>> ['a','b','c'] >> skip(1)
        ['b', 'c']
        >>> [('a',1),('b',2),('c',3)] | skip(1).tolist()
        [('b', 2), ('c', 3)]
        >>> [{'key':'a','val':1},{'key':'b','val':2},{'key':'c','val':3}] | skip(1).tolist()
        [{'val': 2, 'key': 'b'}, {'val': 3, 'key': 'c'}]
    """
    @classmethod
    def op(cls,text,lines,*args,**kwargs):
        for i,line in enumerate(cls._tolist(text)):
            if i >= lines:
                yield line

class tail(TextOp):
    r"""Return last lines from the input text

    Args:
        lines(int): The number of lines/items to return.

    Yields:
        str, lists or dicts: the last 'lines' lines from the input text

    Examples:
        >>> 'a\nb\nc' | tail(2).tostr()
        'b\nc'
        >>> for l in 'a\nb\nc' | tail(2):
        ...   print l
        b
        c
        >>> ['a','b','c'] | tail(2).tolist()
        ['b', 'c']
        >>> ['a','b','c'] >> tail(2)
        ['b', 'c']
        >>> [('a',1),('b',2),('c',3)] | tail(2).tolist()
        [('b', 2), ('c', 3)]
        >>> [{'key':'a','val':1},{'key':'b','val':2},{'key':'c','val':3}] | tail(2).tolist()
        [{'val': 2, 'key': 'b'}, {'val': 3, 'key': 'c'}]
    """
    @classmethod
    def op(cls,text,lines,*args,**kwargs):
        buffer = []
        for line in cls._tolist(text):
            buffer.append(line)
            if len(buffer) > lines:
                buffer.pop(0)
        for line in buffer:
            yield line

class sed(TextOp):
    r"""Replace pattern on-the-fly

    Works like the shell command 'sed'. It uses :func:`re.sub` to replace the pattern, this means that
    you can include back-reference into the replacement string.

    Args:
        pat(str): a string (case sensitive) or a regular expression for the pattern to search
        repl(str): the replace string.

    Yields:
        str: the replaced lines from the input text

    Examples:
        >>> 'Hello Eric\nHello Guido' | sed('Hello','Bonjour').tostr()
        'Bonjour Eric\nBonjour Guido'
        >>> [ 'Hello Eric','Hello Guido'] | sed('Hello','Bonjour').tolist()
        ['Bonjour Eric', 'Bonjour Guido']
        >>> [ 'Hello Eric','Hello Guido'] >> sed('Hello','Bonjour')
        ['Bonjour Eric', 'Bonjour Guido']
        >>> [ 'Hello Eric','Hello Guido'] | sed(r'$',' !').tolist()
        ['Hello Eric !', 'Hello Guido !']
        >>> import re
        >>> [ 'Hello Eric','Hello Guido'] | sed(re.compile('hello',re.I),'Good bye').tolist()
        ['Good bye Eric', 'Good bye Guido']
        >>> [ 'Hello Eric','Hello Guido'] | sed('hello','Good bye').tolist()
        ['Hello Eric', 'Hello Guido']
    """
    flags = 0
    @classmethod
    def op(cls,text,pat,repl,*args,**kwargs):
        if isinstance(pat, basestring):
            pat = re.compile(pat,cls.flags)
        for line in cls._tolist(text):
            yield pat.sub(repl,line)

class sedi(sed):
    r"""Replace pattern on-the-fly (case insensitive)

    Works like :class:`textops.sed` except that the string as the search pattern is case insensitive.

    Args:
        pat(str): a string (case insensitive) or a regular expression for the pattern to search
        repl(str): the replace string.

    Yields:
        str: the replaced lines from the input text

    Examples:
        >>> [ 'Hello Eric','Hello Guido'] | sedi('hello','Good bye').tolist()
        ['Good bye Eric', 'Good bye Guido']
        >>> [ 'Hello Eric','Hello Guido'] >> sedi('hello','Good bye')
        ['Good bye Eric', 'Good bye Guido']
    """
    flags = re.IGNORECASE

class between(TextOp):
    r"""Extract lines between two patterns

    It will search for the starting pattern then yield lines until it reaches the ending pattern.
    Pattern can be a string or a Regex object, it can be also a list of strings or Regexs,
    in this case, all patterns in the list must be matched in the same order, this may be useful
    to better select some part of the text in some cases.

    ``between`` works for any kind of list of strings, but also for list of lists and list of dicts.
    In these cases, one can test only one column or one key but return the whole list/dict.

    Args:
        begin(str or regex or list): the pattern(s) to reach before yielding lines from the input
        end(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the begin pattern (Default : False)
        get_end(bool): if True : include the line matching the end pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines between two patterns

    Examples:
        >>> 'a\nb\nc\nd\ne\nf' | between('b','e').tostr()
        'c\nd'
        >>> 'a\nb\nc\nd\ne\nf' | between('b','e',True,True).tostr()
        'b\nc\nd\ne'
        >>> ['a','b','c','d','e','f'] | between('b','e').tolist()
        ['c', 'd']
        >>> ['a','b','c','d','e','f'] >> between('b','e')
        ['c', 'd']
        >>> ['a','b','c','d','e','f'] | between('b','e',True,True).tolist()
        ['b', 'c', 'd', 'e']
        >>> input_text = [('a',1),('b',2),('c',3),('d',4),('e',5),('f',6)]
        >>> input_text | between('b','e').tolist()
        [('c', 3), ('d', 4)]
        >>> input_text = [{'a':1},{'b':2},{'c':3},{'d':4},{'e':5},{'f':6}]
        >>> input_text | between('b','e').tolist()
        [{'c': 3}, {'d': 4}]
        >>> input_text = [{'k':1},{'k':2},{'k':3},{'k':4},{'k':5},{'k':6}]
        >>> input_text | between('2','5',col_or_key='k').tolist()
        [{'k': 3}, {'k': 4}]
        >>> input_text = [{'k':1},{'k':2},{'k':3},{'k':4},{'k':5},{'k':6}]
        >>> input_text | between('2','5',col_or_key='v').tolist()
        []
        >>> input_text = [('a',1),('b',2),('c',3),('d',4),('e',5),('f',6)]
        >>> input_text | between('b','e',col_or_key=0).tolist()
        [('c', 3), ('d', 4)]
        >>> input_text = [('a',1),('b',2),('c',3),('d',4),('e',5),('f',6)]
        >>> input_text | between('b','e',col_or_key=1).tolist()
        []
        >>> s='''Chapter 1
        ... ------------
        ... some infos
        ...
        ... Chapter 2
        ... ---------
        ... infos I want
        ...
        ... Chaper 3
        ... --------
        ... some other infos'''
        >>> print s | between('---',r'^\s*$').tostr()
        some infos
        >>> print s | between(['Chapter 2','---'],r'^\s*$').tostr()
        infos I want
    """
    flags = 0
    boundaries = False
    @classmethod
    def _build_regex_list(cls,string_or_list):
        if string_or_list is None:
            return []
        elif isinstance(string_or_list, basestring):
            lst = [string_or_list]
        else:
            lst = list(string_or_list)
        return [ re.compile(pat,cls.flags) if isinstance(pat, basestring) else pat for pat in lst ]

    @classmethod
    def op(cls, text, begin, end, get_begin=None, get_end=None, col_or_key=None, *args,**kwargs):
        if get_begin is None:
            get_begin = cls.boundaries
        if get_end is None:
            get_end = cls.boundaries
        begin = cls._build_regex_list(begin)
        end = cls._build_regex_list(end)

        state = 0 if begin else 1

        for line in cls._tolist(text):
            try:
                to_test = line if col_or_key is None else line[col_or_key]
                to_test = to_test if isinstance(to_test, basestring) else str(to_test)
                if state == 0 and begin:
                    if begin[0].search(to_test):
                        begin.pop(0)
                    if not begin:
                        if get_begin:
                            yield line
                        state = 1
                elif state == 1 and end:
                    if end[0].search(to_test):
                        end.pop(0)
                    if not end:
                        if get_end:
                            yield line
                        break
                    else:
                        yield line
                else:
                    yield line
            except (ValueError, TypeError, IndexError, KeyError):
                pass

class betweeni(between):
    r"""Extract lines between two patterns (case insensitive)

    Works like :class:`textops.between` except patterns are case insensitive

    Args:
        begin(str or regex or list): the pattern(s) to reach before yielding lines from the input
        end(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the begin pattern (Default : False)
        get_end(bool): if True : include the line matching the end pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines between two patterns

    Examples:
        >>> ['a','b','c','d','e','f'] | between('B','E').tolist()
        []
        >>> ['a','b','c','d','e','f'] | betweeni('B','E').tolist()
        ['c', 'd']
        >>> ['a','b','c','d','e','f'] >> betweeni('B','E')
        ['c', 'd']
    """
    flags = re.IGNORECASE

class betweenb(between):
    r"""Extract lines between two patterns (includes boundaries)

    Works like :class:`textops.between` except it return boundaries by default that is
    get_begin = get_end = True.

    Args:
        begin(str or regex or list): the pattern(s) to reach before yielding lines from the input
        end(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the begin pattern (Default : False)
        get_end(bool): if True : include the line matching the end pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines between two patterns

    Examples:
        >>> ['a','b','c','d','e','f'] | betweenb('b','e').tolist()
        ['b', 'c', 'd', 'e']
        >>> ['a','b','c','d','e','f'] >> betweenb('b','e')
        ['b', 'c', 'd', 'e']
    """
    boundaries = True

class betweenbi(betweenb):
    r"""Extract lines between two patterns (includes boundaries and case insensitive)

    Works like :class:`textops.between` except patterns are case insensitive and it yields boundaries too.
    That is get_begin = get_end = True.

    Args:
        begin(str or regex or list): the pattern(s) to reach before yielding lines from the input
        end(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the begin pattern (Default : False)
        get_end(bool): if True : include the line matching the end pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines between two patterns

    Examples:
        >>> ['a','b','c','d','e','f'] | betweenb('B','E').tolist()
        []
        >>> ['a','b','c','d','e','f'] | betweenbi('B','E').tolist()
        ['b', 'c', 'd', 'e']
        >>> ['a','b','c','d','e','f'] >> betweenbi('B','E')
        ['b', 'c', 'd', 'e']
    """
    flags = re.IGNORECASE

class linetester(TextOp):
    r""" Abstract class for by-line testing"""
    @classmethod
    def testline(cls, to_test, *args,**kwargs):
        raise AssertionError('Method testline must be defined in derivated class.')

    @classmethod
    def cast_to(cls, *args, **kwargs):
        return type(args[0])

    @classmethod
    def op(cls, text, *args,**kwargs):
        col_or_key = kwargs.get('col_or_key')
        cast_to = cls.cast_to(*args,**kwargs)
        for line in cls._tolist(text):
            try:
                to_test = line if col_or_key is None else line[col_or_key]
                to_test = cast_to(to_test)
                if cls.testline(to_test, *args,**kwargs):
                    yield line
            except (ValueError, TypeError, IndexError, KeyError):
                pass

class inrange(linetester):
    r"""Extract lines between a range of strings

    For each input line, it tests whether it is greater or equal than ``begin`` argument and
    strictly less than ``end`` argument. At the opposite of textops.between_, there no need to
    match begin or end string.

    ``inrange`` works for any kind of list of strings, but also for list of lists and list of dicts.
    In these cases, one can test only one column or one key but return the whole list/dict.

    Each strings that will be tested is converted with the same type of the first argument.

    Args:
        begin(str): range begin string
        end(str): range end string
        get_begin(bool): if True : include lines having the same value as the range begin,
            Default : True
        get_end(bool): if True : include lines having the same value as the range end,
            Default : False
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values inside the specified range

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | inrange('2015-08-12','2015-11-05').tolist()
        ['2015-08-23 bbbb', '2015-09-14 ccc']
        >>> logs >> inrange('2015-08-12','2015-11-05')
        ['2015-08-23 bbbb', '2015-09-14 ccc']
        >>> logs = [ ('aaaa','2015-08-11'),
        ... ('bbbb','2015-08-23'),
        ... ('ccc','2015-09-14'),
        ... ('ddd','2015-11-05') ]
        >>> logs | inrange('2015-08-12','2015-11-05',col_or_key=1).tolist()
        [('bbbb', '2015-08-23'), ('ccc', '2015-09-14')]
        >>> logs = [ {'data':'aaaa','date':'2015-08-11'},
        ... {'data':'bbbb','date':'2015-08-23'},
        ... {'data':'ccc','date':'2015-09-14'},
        ... {'data':'ddd','date':'2015-11-05'} ]
        >>> logs | inrange('2015-08-12','2015-11-05',col_or_key='date').tolist()
        [{'date': '2015-08-23', 'data': 'bbbb'}, {'date': '2015-09-14', 'data': 'ccc'}]
        >>> ints = '1\n2\n01\n02\n11\n12\n22\n20'
        >>> ints | inrange(1,3).tolist()
        ['1', '2', '01', '02']
        >>> ints | inrange('1','3').tolist()
        ['1', '2', '11', '12', '22', '20']
        >>> ints | inrange('1','3',get_begin=False).tolist()
        ['2', '11', '12', '22', '20']
    """
    @classmethod
    def testline(cls, to_test,  begin, end, get_begin=True, get_end=False, *args,**kwargs):
        return  (to_test > begin and to_test < end) or \
                (to_test == begin and get_begin) or \
                (to_test == end and get_end)


class outrange(linetester):
    r"""Extract lines NOT between a range of strings

    Works like :class:`textops.inrange` except it yields lines that are NOT in the range

    Args:
        begin(str): range begin string
        end(str): range end string
        get_begin(bool): if True : include lines having the same value as the range begin,
            Default : False
        get_end(bool): if True : include lines having the same value as the range end,
            Default : False
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values outside the specified range

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | outrange('2015-08-12','2015-11-05').tolist()
        ['2015-08-11 aaaa', '2015-11-05 ddd']
        >>> logs | outrange('2015-08-23 bbbb','2015-09-14 ccc').tolist()
        ['2015-08-11 aaaa', '2015-11-05 ddd']
        >>> logs | outrange('2015-08-23 bbbb','2015-09-14 ccc', get_begin=True).tolist()
        ['2015-08-11 aaaa', '2015-08-23 bbbb', '2015-11-05 ddd']
    """
    @classmethod
    def testline(cls, to_test,  begin, end, get_begin=False, get_end=False, *args,**kwargs):
        return       to_test < begin or to_test > end or \
                     (to_test == begin and get_begin) or \
                     (to_test == end and get_end)

class lessthan(linetester):
    r"""Extract lines with value strictly less than specified string

    It works for any kind of list of strings, but also for list of lists and list of dicts.
    In these cases, one can test only one column or one key but return the whole list/dict.

    Each strings that will be tested is temporarily converted with the same type as the first
    argument given to ``lessthan`` (see examples).

    Args:
        value(str): string to test with
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values strictly less than the specified reference value

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | lessthan('2015-09-14').tolist()
        ['2015-08-11 aaaa', '2015-08-23 bbbb']
        >>> logs = [ ('aaaa','2015-08-11'),
        ... ('bbbb','2015-08-23'),
        ... ('ccc','2015-09-14'),
        ... ('ddd','2015-11-05') ]
        >>> logs | lessthan('2015-11-05',col_or_key=1).tolist()
        [('aaaa', '2015-08-11'), ('bbbb', '2015-08-23'), ('ccc', '2015-09-14')]
        >>> logs = [ {'data':'aaaa','date':'2015-08-11'},
        ... {'data':'bbbb','date':'2015-08-23'},
        ... {'data':'ccc','date':'2015-09-14'},
        ... {'data':'ddd','date':'2015-11-05'} ]
        >>> logs | lessthan('2015-09-14',col_or_key='date').tolist()
        [{'date': '2015-08-11', 'data': 'aaaa'}, {'date': '2015-08-23', 'data': 'bbbb'}]
        >>> ints = '1\n2\n01\n02\n11\n12\n22\n20'
        >>> ints | lessthan(3).tolist()
        ['1', '2', '01', '02']
        >>> ints | lessthan('3').tolist()
        ['1', '2', '01', '02', '11', '12', '22', '20']
        """
    @classmethod
    def testline(cls, to_test, value, *args,**kwargs):
        return to_test < value

class lessequal(linetester):
    r"""Extract lines with value strictly less than specified string

    It works like :class:`textops.lessthan` except the test is "less or equal"

    Args:
        value(str): string to test with
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values less than or equal to the specified value

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | lessequal('2015-09-14').tolist()
        ['2015-08-11 aaaa', '2015-08-23 bbbb']
        >>> logs >> lessequal('2015-09-14')
        ['2015-08-11 aaaa', '2015-08-23 bbbb']
        >>> logs | lessequal('2015-09-14 ccc').tolist()
        ['2015-08-11 aaaa', '2015-08-23 bbbb', '2015-09-14 ccc']
        """
    @classmethod
    def testline(cls, to_test, value, *args,**kwargs):
        return to_test <= value

class greaterthan(linetester):
    r"""Extract lines with value strictly less than specified string

    It works like :class:`textops.lessthan` except the test is "greater than"

    Args:
        value(str): string to test with
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values greater than the specified value

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | greaterthan('2015-09-14 ccc').tolist()
        ['2015-11-05 ddd']
        >>> logs >> greaterthan('2015-09-14 ccc')
        ['2015-11-05 ddd']
        """
    @classmethod
    def testline(cls, to_test, value, *args,**kwargs):
        return to_test > value

class greaterequal(linetester):
    r"""Extract lines with value strictly less than specified string

    It works like :class:`textops.greaterthan` except the test is "greater than or equal to"

    Args:
        value(str): string to test with
        col_or_key (int or str): test only one column or one key (optional).
            it *MUST BE PASSED BY NAME* if you want to use this argument.

    Yields:
        str or list or dict: lines having values greater than or equal to the specified value

    Examples:
        >>> logs = '''2015-08-11 aaaa
        ... 2015-08-23 bbbb
        ... 2015-09-14 ccc
        ... 2015-11-05 ddd'''
        >>> logs | greaterequal('2015-09-14 ccc').tolist()
        ['2015-09-14 ccc', '2015-11-05 ddd']
        >>> logs >> greaterequal('2015-09-14 ccc')
        ['2015-09-14 ccc', '2015-11-05 ddd']
        """
    @classmethod
    def testline(cls, to_test, value, *args,**kwargs):
        return to_test >= value

class before(between):
    r"""Extract lines before a patterns

    Works like :class:`textops.between` except that it requires only the ending pattern : it will yields
    all lines from the input text beginning until the specified pattern has been reached.

    Args:
        pattern(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_end(bool): if True : include the line matching the end pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines before the specified pattern

    Examples:
        >>> ['a','b','c','d','e','f'] | before('c').tolist()
        ['a', 'b']
        >>> ['a','b','c','d','e','f'] | before('c',True).tolist()
        ['a', 'b', 'c']
        >>> input_text = [{'k':1},{'k':2},{'k':3},{'k':4},{'k':5},{'k':6}]
        >>> input_text | before('3',col_or_key='k').tolist()
        [{'k': 1}, {'k': 2}]
        >>> input_text >> before('3',col_or_key='k')
        [{'k': 1}, {'k': 2}]
    """
    @classmethod
    def op(cls, text, pattern, get_end=False, col_or_key=None,*args,**kwargs):
        return super(before,cls).op(text,None,pattern,get_end=get_end,col_or_key=col_or_key)

class beforei(before):
    r"""Extract lines before a patterns (case insensitive)

    Works like :class:`textops.before` except that the pattern is case insensitive.

    Args:
        pattern(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_end(bool): if True : include the line matching the pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines before the specified pattern

    Examples:
        >>> ['a','b','c','d','e','f'] | before('C').tolist()
        ['a', 'b', 'c', 'd', 'e', 'f']
        >>> ['a','b','c','d','e','f'] | beforei('C').tolist()
        ['a', 'b']
        >>> ['a','b','c','d','e','f'] | beforei('C',True).tolist()
        ['a', 'b', 'c']
        >>> ['a','b','c','d','e','f'] >> beforei('C',True)
        ['a', 'b', 'c']
    """
    flags = re.IGNORECASE

class after(between):
    r"""Extract lines after a patterns

    Works like :class:`textops.before` except that it will yields all lines from the input AFTER the given
    pattern has been found.

    Args:
        pattern(str or regex or list): start yielding lines after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines after the specified pattern

    Examples:
        >>> ['a','b','c','d','e','f'] | after('c').tolist()
        ['d', 'e', 'f']
        >>> ['a','b','c','d','e','f'] | after('c',True).tolist()
        ['c', 'd', 'e', 'f']
        >>> input_text = [{'k':1},{'k':2},{'k':3},{'k':4},{'k':5},{'k':6}]
        >>> input_text | after('3',col_or_key='k').tolist()
        [{'k': 4}, {'k': 5}, {'k': 6}]
        >>> input_text >> after('3',col_or_key='k')
        [{'k': 4}, {'k': 5}, {'k': 6}]
    """
    @classmethod
    def op(cls, text, pattern, get_begin=False,*args,**kwargs):
        return super(after,cls).op(text,pattern,None,get_begin=get_begin)

class afteri(after):
    r"""Extract lines after a patterns (case insensitive)

    Works like :class:`textops.after` except that the pattern is case insensitive.

    Args:
        pattern(str or regex or list): no more lines are yield after reaching this pattern(s)
        get_begin(bool): if True : include the line matching the pattern (Default : False)
        col_or_key (int or str): test only one column or one key (optional)

    Yields:
        str or list or dict: lines before the specified pattern

    Examples:
        >>> ['a','b','c','d','e','f'] | after('C').tolist()
        []
        >>> ['a','b','c','d','e','f'] | afteri('C').tolist()
        ['d', 'e', 'f']
        >>> ['a','b','c','d','e','f'] | afteri('C',True).tolist()
        ['c', 'd', 'e', 'f']
        >>> ['a','b','c','d','e','f'] >> afteri('C',True)
        ['c', 'd', 'e', 'f']
    """
    flags = re.IGNORECASE

class mapfn(TextOp):
    r"""Apply a specified function on every line

    It works like the python map() function.

    Args:
        map_fn(callable): a function or a callable to apply on every line

    Yields:
        any: lines modified by the map_fn function

    Examples:
        >>> ['a','b','c'] | mapfn(lambda l:l*2).tolist()
        ['aa', 'bb', 'cc']
        >>> ['a','b','c'] >> mapfn(lambda l:l*2)
        ['aa', 'bb', 'cc']
    """
    @classmethod
    def op(cls, text, map_fn, *args,**kwargs):
        for line in cls._tolist(text):
            yield map_fn(line)

class iffn(TextOp):
    r"""Filters the input text with a specified function

    It works like the python filter() fonction.

    Args:
        filter_fn(callable): a function to be called against each line and returning a boolean.
        True means : yield the line.

    Yields:
        any: lines filtered by the filter_fn function

    Examples:
        >>> import re
        >>> 'line1\nline2\nline3\nline4' | iffn(lambda l:int(re.sub(r'\D','',l)) % 2).tolist()
        ['line1', 'line3']
        >>> 'line1\nline2\nline3\nline4' >> iffn(lambda l:int(re.sub(r'\D','',l)) % 2)
        ['line1', 'line3']
    """
    @classmethod
    def op(cls, text, filter_fn=None, *args,**kwargs):
        if filter_fn is None:
            filter_fn = lambda x:x
        for line in cls._tolist(text):
            if filter_fn(line):
                yield line

class mapif(TextOp):
    r"""Filters and maps the input text with 2 specified functions

    Filters input text AND apply a map function on every filtered lines.

    Args:
        map_fn(callable): a function or a callable to apply on every line to be yield
        filter_fn(callable): a function to be called against each line and returning a boolean.
        True means : yield the line.

    Yields:
        any: lines filtered by the filter_fn function and modified by map_fn function

    Examples:
        >>> import re
        >>> 'a1\nb2\nc3\nd4' | mapif(lambda l:l*2,lambda l:int(re.sub(r'\D','',l)) % 2).tolist()
        ['a1a1', 'c3c3']
        >>> 'a1\nb2\nc3\nd4' >> mapif(lambda l:l*2,lambda l:int(re.sub(r'\D','',l)) % 2)
        ['a1a1', 'c3c3']
    """
    @classmethod
    def op(cls, text, map_fn, filter_fn=None,*args,**kwargs):
        if filter_fn is None:
            filter_fn = lambda x:x
        for line in cls._tolist(text):
            if filter_fn(line):
                yield map_fn(line)

class doreduce(TextOp):
    r"""Reduce the input text

    Uses python reduce() function.

    Args:
        reduce_fn(callable): a function or a callable to reduce every line.
        initializer(object): initial accumulative value (Default : None)

    Returns:
        any: reduced value

    Examples:
        >>> import re
        >>> 'a1\nb2\nc3\nd4' | doreduce(lambda x,y:x+re.sub(r'\d','',y),'')
        'abcd'
        >>> 'a1\nb2\nc3\nd4' >> doreduce(lambda x,y:x+re.sub(r'\d','',y),'')
        'abcd'
    """
    @classmethod
    def op(cls, text, reduce_fn, initializer=None, *args, **kwargs):
        return reduce(reduce_fn, cls._tolist(text), initializer)

class merge_dicts(TextOp):
    r"""Merge a list of dicts into one single dict

    Returns:
        dict: merged dicts

    Examples:
        >>> pattern=r'item="(?P<item>[^"]*)" count="(?P<i_count>[^"]*)" price="(?P<i_price>[^"]*)"'
        >>> s='item="col1" count="col2" price="col3"\nitem="col11" count="col22" price="col33"'
        >>> s | cutkv(pattern,key_name='item')                                                      # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        [{'col1': {'item': 'col1', 'i_price': 'col3', 'i_count': 'col2'}},...
        {'col11': {'item': 'col11', 'i_price': 'col33', 'i_count': 'col22'}}]
        >>> s | cutkv(pattern,key_name='item').merge_dicts()                                        # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        {'col11': {'item': 'col11', 'i_price': 'col33', 'i_count': 'col22'},...
        'col1': {'item': 'col1', 'i_price': 'col3', 'i_count': 'col2'}}
    """
    @classmethod
    def op(cls,text,*args,**kwargs):
        out = {}
        for dct in cls._tolist(text):
            if isinstance(dct, dict):
                out.update(dct)
        return out

class span(TextOp):
    r"""Ensure that a list of lists has exactly the specified number of column

    This is useful in for-loop with multiple assignment

    Args:
        nbcols(int): number columns to return
        fill_str(str): the value to return for not exsiting columns

    Returns:
        list: A list with exactly ``nbcols`` columns

    Examples:
        >>> s='a\nb c\nd e f g h\ni j k\n\n'
        >>> s | cut()
        [['a'], ['b', 'c'], ['d', 'e', 'f', 'g', 'h'], ['i', 'j', 'k'], []]
        >>> s | cut().span(3,'-').tolist()
        [['a', '-', '-'], ['b', 'c', '-'], ['d', 'e', 'f'], ['i', 'j', 'k'], ['-', '-', '-']]
        >>> s >> cut().span(3,'-')
        [['a', '-', '-'], ['b', 'c', '-'], ['d', 'e', 'f'], ['i', 'j', 'k'], ['-', '-', '-']]
        >>> for x,y,z in s | cut().span(3,'-'):
        ...    print x,y,z
        a - -
        b c -
        d e f
        i j k
        - - -
    """
    @classmethod
    def op(cls, text, nbcols, fill_str='', *args,**kwargs):
        fill_list = [fill_str] * nbcols
        for sublist in cls._tolist(text):
            yield (sublist+fill_list)[:nbcols]

class doslice(TextOp):
    r"""Get lines/items from ``begin`` line to ``end`` line with some ``step``

    Args:
        begin(int): first line number to get.
            must be None or an integer: 0 <= x <= maxint
        end(int): end line number (get lines up to end - 1).
            must be None or an integer: 0 <= x <= maxint
        step(int): get every ``step`` line (Default : 1)

    Returns:
        generator: A slice of the original text

    Examples:
        >>> s='a\nb\nc\nd\ne\nf'
        >>> s | doslice(1,4).tolist()
        ['b', 'c', 'd']
        >>> s >> doslice(1,4)
        ['b', 'c', 'd']
        >>> s >> doslice(2)
        ['c', 'd', 'e', 'f']
        >>> s >> doslice(0,4,2)
        ['a', 'c']
        >>> s >> doslice(None,None,2)
        ['a', 'c', 'e']
    """
    @classmethod
    def op(cls, text, begin=0, end=sys.maxsize, step = 1, *args,**kwargs):
        for line in itertools.islice(cls._tolist(text), begin, end, step):
            yield line

class subslice(TextOp):
    r"""Get a slice of columns for list of lists

    Args:
        begin(int): first columns number to get.
            must be None or an integer: 0 <= x <= maxint
        end(int): end columns number (get columns up to end - 1).
            must be None or an integer: 0 <= x <= maxint
        step(int): get every ``step`` columns (Default : 1)

    Returns:
        generator: A slice of the original text

    Examples:
        >>> s='a\nb c\nd e f g h\ni j k\n\n'
        >>> s | cut().span(3,'-').tolist()
        [['a', '-', '-'], ['b', 'c', '-'], ['d', 'e', 'f'], ['i', 'j', 'k'], ['-', '-', '-']]
        >>> s | cut().span(3,'-').subslice(1,3).tolist()
        [['-', '-'], ['c', '-'], ['e', 'f'], ['j', 'k'], ['-', '-']]
        >>> s >> cut().span(3,'-').subslice(1,3)
        [['-', '-'], ['c', '-'], ['e', 'f'], ['j', 'k'], ['-', '-']]
    """
    @classmethod
    def op(cls, text, begin=0, end=sys.maxsize, step = 1, *args,**kwargs):
        for sublist in cls._tolist(text):
            yield sublist[begin:end:step]

class subitem(TextOp):
    r"""Get a specified column for list of lists

    Args:
        n(int): column number to get.

    Returns:
        generator: A list

    Examples:
        >>> s='a\nb c\nd e f g h\ni j k\n\n'
        >>> s | cut().span(3,'-').tolist()
        [['a', '-', '-'], ['b', 'c', '-'], ['d', 'e', 'f'], ['i', 'j', 'k'], ['-', '-', '-']]
        >>> s | cut().span(3,'-').subitem(1).tolist()
        ['-', 'c', 'e', 'j', '-']
        >>> s >> cut().span(3,'-').subitem(1)
        ['-', 'c', 'e', 'j', '-']
        >>> s >> cut().span(3,'-').subitem(-1)
        ['-', '-', 'f', 'k', '-']
    """
    @classmethod
    def op(cls, text, n, *args,**kwargs):
        for sublist in cls._tolist(text):
            yield sublist[n]

class subitems(TextOp):
    r"""Get the specified columns for list of lists

    Args:
        ntab(list of int): columns numbers to get.

    Returns:
        generator: A list of lists

    Examples:
        >>> s='a\nb c\nd e f g h\ni j k\n\n'
        >>> s | cut().span(3,'-').tolist()
        [['a', '-', '-'], ['b', 'c', '-'], ['d', 'e', 'f'], ['i', 'j', 'k'], ['-', '-', '-']]
        >>> s | cut().span(3,'-').subitems([0,2]).tolist()
        [['a', '-'], ['b', '-'], ['d', 'f'], ['i', 'k'], ['-', '-']]
        >>> s >> cut().span(3,'-').subitems('0,2')
        [['a', '-'], ['b', '-'], ['d', 'f'], ['i', 'k'], ['-', '-']]
    """
    @classmethod
    def op(cls, text, ntab, *args,**kwargs):
        if isinstance(ntab,basestring):
            ntab = [ int(n) for n in ntab.split(',') ]
        for sublist in cls._tolist(text):
            yield [ sublist[n] for n in ntab ]

class uniq(TextOp):
    r"""Remove all line repetitions

    If a line is many times in the same text (even if there are some different lines between),
    only the first will be taken. Works also with list of lists or dicts.

    Returns:
        generator: Unified text line by line.

    Examples:
        >>> s='f\na\nb\na\nc\nc\ne\na\nc\nf'
        >>> s >> uniq()
        ['f', 'a', 'b', 'c', 'e']
        >>> for line in s | uniq():
        ...     print line
        f
        a
        b
        c
        e
        >>> l = [ [1,2], [3,4], [1,2] ]
        >>> l >> uniq()
        [[1, 2], [3, 4]]
        >>> d = [ {'a':1}, {'b':2}, {'a':1} ]
        >>> d >> uniq()
        [{'a': 1}, {'b': 2}]
    """
    @classmethod
    def op(cls, text, *args,**kwargs):
        s=[]
        for line in cls._tolist(text):
            if line not in s:
                s.append(line)
                yield line
