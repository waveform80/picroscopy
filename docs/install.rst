.. _install:

============
Installation
============

To install the application from PyPI into an existing Raspbian image, first
ensure you install the pre-requisites::

    $ sudo apt-get install build-essential exuberant-ctags python3-dev \
        python-virtualenv libjpeg8-dev libtiff5-dev libfreetype6-dev zlib1g-dev

Next, create a virtual Python 3 environment from which to run Picroscopy (this
avoids having to install anything as root which makes it easier to remove later
should you wish to start over)::

    $ virtualenv -p python3 picroscopyenv
    $ source picroscopyenv/bin/activate

Finally, install Picroscopy within the environment::

    $ easy_install picroscopy


Development
===========

The system relies on several third party libraries, including Pillow a fork of
the Python Imaging Library (PIL) which requires some compilation. On Raspbian,
first ensure you install all the pre-requisites::

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

You should now be able to run picroscopy with one of the included configuration
files like so::

    $ picroscopy -c development.ini


