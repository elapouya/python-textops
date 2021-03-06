..
   Created : 2015-11-04

   @author: Eric Lapouyade

   python-textops documentation master file,


.. image:: images/textops_logo.png
   :align: center

|
| `python-textops <http://python-textops.readthedocs.org>`_ provides many text operations at string level, list level or whole text level.
| These operations can be chained with a 'dotted' or 'piped' notation.
| Chained operations are stored into a single lazy object, they will be executed only when an input text will be provided.

Here is a simple example to count number of mails received from spammer@hacker.com since May 25th::

   >>> '/var/log/mail.log' | cat().grep('spammer@hacker.com').since('May 25').lcount()
   37

python-textops is used into some other projects like `python-nagios-helpers <http://python-nagios-helpers.readthedocs.org>`_

.. toctree::
   :maxdepth: 1

   intro
   strops
   listops
   fileops
   runops
   wrapops
   parse
   cast
   recode
   base

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

