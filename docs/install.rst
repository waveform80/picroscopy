.. _install:

============
Installation
============

To install the application from PyPI into an existing `Raspbian`_ image, first
ensure you install the pre-requisites::

    $ sudo apt-get install build-essential python3-dev python-virtualenv \
      libjpeg8-dev libtiff5-dev libfreetype6-dev zlib1g-dev

Next, create a virtual Python 3 environment from which to run Picroscopy (this
avoids having to install anything as root which makes it easier to remove later
should you wish to start over)::

    $ virtualenv -p python3 picroscopyenv
    $ source picroscopyenv/bin/activate

Finally, install Picroscopy within the environment::

    $ easy_install picroscopy

If you wish to install the documentation building dependencies also::

    $ easy_install picroscopy[doc]

.. warning::
    If you install picroscopy with the optional ``[doc]`` specifier (which
    installs the dependencies required to build the documentation), the
    installation will take an *extremely* long time to build on the Pi.

    `Sphinx`_ and `docutils`_, which are used for the documentation, take
    nearly an hour to build; this seems to have something to do with their use
    of ``2to3`` to attain Python 3 compatibility.

You should now be able to run picroscopy with the included configuration file
like so::

    $ picroscopy -c picroscopy.ini


Development
===========

The system relies on several third party libraries including `Pillow`_, a fork
of the `Python Imaging Library`_ (PIL) which requires some compilation. On
`Raspbian`_, first ensure you install all the pre-requisites::

    $ sudo apt-get install build-essential exuberant-ctags python3-dev \
        python-virtualenv libjpeg8-dev libtiff5-dev libfreetype6-dev zlib1g-dev

Next, create a virtual python environment from which to run Picroscopy and
activate it::

    $ virtualenv -p python3 picroscopyenv
    $ source picroscopyenv/bin/activate

Finally, grab a copy of the Picroscopy source from GitHub and install it into
the virtualenv (the example below uses the ``develop`` target for development
purposes; you can use ``install`` if you just wish to install Picroscopy
without any of the extra development stuff like tags)::

    $ git clone https://github.com/waveform80/picroscopy.git
    $ cd picroscopy
    $ make develop

You should now be able to run picroscopy with the included configuration file
like so::

    $ picroscopy -c picroscopy.ini

If you wish to develop the documentation, please be aware of the warning above
about long installation times. You can use the following make target to build
the documentation in all available formats (output will be under
``build/sphinx/{html,latex,man,...}``)::

    $ make doc

If you wish to run the test suite (currently non-existent!) use the following
make target::

    $ make test


.. _Raspbian: http://www.raspbian.org/
.. _Pillow: http://pypi.python.org/pypi/Pillow
.. _Python Imaging Library: http://www.pythonware.com/products/pil/
.. _Sphinx: http://sphinx-doc.org/
.. _docutils: http://docutils.sourceforge.net/
