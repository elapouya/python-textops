..
   Created : 2015-11-04

   @author: Eric Lapouyade

=======
listops
=======
.. automodule:: textops.ops.listops
.. currentmodule:: textops

after
-----
   .. autoclass:: after(pattern, get_begin=False, key=None)

afteri
------
   .. autoclass:: afteri(pattern, get_begin=False, key=None)

before
------
   .. autoclass:: before(pattern, get_end=False, key=None)

beforei
-------
   .. autoclass:: beforei(pattern, get_end=False, key=None)

between
-------
   .. autoclass:: between(begin, end, get_begin=False, get_end=False, key=None)

betweeni
--------
   .. autoclass:: betweeni(begin, end, get_begin=False, get_end=False, key=None)

betweenb
--------
   .. autoclass:: betweenb(begin, end, get_begin=False, get_end=False, key=None)

betweenbi
---------
   .. autoclass:: betweenbi(begin, end, get_begin=False, get_end=False, key=None)

cat
---
   .. autoclass:: cat(context={})

doreduce
--------
   .. autoclass:: doreduce(reduce_fn, initializer=None)

doslice
-------
   .. autoclass:: doslice(begin=0, end=sys.maxsize, step=1)

first
-----
   .. autoclass:: first( )

formatdicts
-----------
   .. autoclass:: formatdicts(format_str='{key} : {val}\\n',join_str = '',defvalue='-')

formatitems
-----------
   .. autoclass:: formatitems(format_str='{0} : {1}\\n',join_str = '')

formatlists
-----------
   .. autoclass:: formatlists(format_str='{0} : {1}\\n',join_str = '')

greaterequal
------------
   .. autoclass:: greaterequal(value, key=None)

greaterthan
-----------
   .. autoclass:: greaterthan(value, key=None)

grep
----
   .. autoclass:: grep(pattern, key=None)

grepi
-----
   .. autoclass:: grepi(pattern, key=None)

grepv
-----
   .. autoclass:: grepv(pattern, key=None)

grepvi
------
   .. autoclass:: grepvi(pattern, key=None)

grepc
-----
   .. autoclass:: grepc(pattern, key=None)

grepci
------
   .. autoclass:: grepci(pattern, key=None)

grepcv
------
   .. autoclass:: grepcv(pattern, key=None)

grepcvi
-------
   .. autoclass:: grepcvi(pattern, key=None)

haspattern
----------
   .. autoclass:: haspattern(pattern, key=None)

haspatterni
-----------
   .. autoclass:: haspatterni(pattern, key=None)

head
----
   .. autoclass:: head(lines)

iffn
----
   .. autoclass:: iffn(filter_fn=None)

inrange
-------
   .. autoclass:: inrange(begin, end, get_begin=True, get_end=False, key=None)

last
----
   .. autoclass:: last( )

lessequal
---------
   .. autoclass:: lessequal(value, key=None)

lessthan
--------
   .. autoclass:: lessthan(value, key=None)

merge_dicts
-----------
   .. autoclass:: merge_dicts()

mapfn
-----
   .. autoclass:: mapfn(map_fn)

mapif
-----
   .. autoclass:: mapif(map_fn, filter_fn=None)

mrun
----
   .. autoclass:: mrun(context={})

outrange
--------
   .. autoclass:: outrange(begin, end, get_begin=False, get_end=False, key=None)

resplitblock
------------
   .. autoclass:: resplitblock(pattern, include_separator=0, skip_first=False)

run
---
   .. autoclass:: run(context={})

sed
---
   .. autoclass:: sed(pat,repl)

sedi
----
   .. autoclass:: sedi(pat,repl)

skip
----
   .. autoclass:: skip(lines)

span
----
   .. autoclass:: span(nbcols, fill_str='')

splitblock
----------
   .. autoclass:: splitblock(pattern, include_separator=0, skip_first=False)

subslice
--------
   .. autoclass:: subslice(begin=0, end=sys.maxsize, step=1)

subitem
-------
   .. autoclass:: subitem(n)

subitems
--------
   .. autoclass:: subitem(ntab)

tail
----
   .. autoclass:: tail(lines)

uniq
----
   .. autoclass:: uniq()

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

