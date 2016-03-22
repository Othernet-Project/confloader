Introduction
============

Confloader was developed to make handling configuration in .ini format easier.
While Python standard library offers the framework for creating an .ini parser
that is fine-tuned to your needs, Confloader developers found that rewriting
the parser each time was tedious, and the basic tools provided by the standard
library insufficient for repeated use.

While Confloader may be as flexible as the ``ConfigParser`` suite from the
standard library, it has a growing number of features to cover majority of 
scenarios that applications may encounter, and offers facilities of combining
and managing collections of configuration file fragments.

Source code
-----------

Confloader source code can be found `on GitHub
<https://github.com/Outernet-Project/confloader>`_ and is released under BSD
license. See the ``LICENSE`` file in the source tree for more information.

Documentation
-------------

.. toctree::
   :maxdepth: 2

    writing_ini
    working_with

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

