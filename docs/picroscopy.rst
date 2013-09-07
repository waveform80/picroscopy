.. _picroscopy:

==========
picroscopy
==========

The picroscopy application launches a live view of the Raspberry Pi's camera
and serves a web application providing control of the camera. Various options
can be used to configure which network clients can access the web application,
and the paths which the camera will use when writing images.


Synopsis
========

::

    picroscopy [-h] [--version] [-c CONFIG] [-q] [-v] [-l FILE] [-P] [-G]
               [-d] [-L HOST[:PORT]] [-C NETWORK[/LEN]] [--images-dir DIR]
               [--thumbs-dir DIR] [--thumbs-size WIDTHxHEIGHT]
               [--email-from USER[@HOST]]
               [--sendmail EXEC | --smtp-server HOST[:PORT]]
               [--raspivid EXEC] [--raspistill EXEC]

Description
===========

.. program:: picroscopy

.. option:: -h, --help

    Show the application's help page, giving a brief description of each
    command line option, and exit.

.. option:: --version

    Show the program's version number and exit.

.. option:: -c CONFIG, --config CONFIG

    Specify the configuration file that the application should load. See the
    :ref:`config` section for more information on the configuration file
    format.

.. option:: -q, --quiet

    Produce less console output. When this is specified, only error messages
    will be visible at the console. By default, warnings and error messages
    are displayed.

.. option:: -v, --verbose

    Produce more console output. When this is specified, information, warning,
    and error messages will be visible at the console. By default, warnings
    and error messages are displayed.

.. option:: -l FILE, --log-file FILE

    Log displayed messages to the specified FILE. The log file will be appended
    to if it already exists. Its format will include the timestamp that the
    message was displayed, and the severity of the message.

.. option:: -P, --pdb

    Run under PuDB (if available) or PDB. This launches Picroscopy within the
    Python debugger for development purposes.

.. option:: -G, --gstreamer

    Use GStreamer instead of the raspivid/raspistill binaries. This option is
    intended to aid development on non-RPi platforms.

.. option:: -L HOST[:PORT], --listen HOST[:PORT]

    The address and port of the interface that Picroscopy will listen on.
    Defaults to 0.0.0.0:80 (when running as root) or 0.0.0.0:8000 (when running
    as a non-root user). The 0.0.0.0 address means "listen on all available
    network interfaces".

.. option:: -C NETWORK[/LEN], --clients NETWORK[/LEN]

    The network that clients must belong to. Clients that do not belong to the
    specified network will be denied access to Picroscopy. Defaults to
    0.0.0.0/0 (all valid addresses).

.. option:: --images-dir DIR

    The directory in which Picroscopy will store images captured by the camera.
    If not specified, defaults to a temporary directory which is destroyed
    upon exit. If the specified directory does not exist, it will be created.

.. option:: --thumbs-dir DIR

    The directory in which Picroscopy will store thumbnails generated from the
    images taken by the camera. If not specified, defaults to a temporary
    directory which is destroyed upon exit. If the specified directory does
    not exist, it will be created. The thumbnails directory *must* be different
    to the images directory.

.. option:: --thumbs-size WIDTHxHEIGHT

    The maximum size for generated thumbnails (the actual size may be smaller
    due to aspect ratio preservation). Defaults to 320x320.

.. option:: --email-from USER[@HOST]

    The address which Picroscopy will use as a From: address when sending
    e-mail. If HOST is not specified, the configuration of the sending SMTP
    server will determine the host associated with the USER.

.. option:: --sendmail EXEC

    Use the specified sendmail binary to send e-mail. This is the preferred
    option for sending e-mail as it (usually) gracefully handles the case where
    the target SMTP server is unavailable. Defaults to /usr/sbin/sendmail.

.. option:: --smtp-server HOST[:PORT]

    Use the specified SMTP smarthost to send e-mail. This should only be used
    if you do not wish to configure a local sendmail binary. If this option
    is specified, it will always override any ``--sendmail`` specification.

.. option:: --raspivid EXEC

    The path to the raspivid binary to use. Defaults to ``/usr/bin/raspivid``.

.. option:: --raspistill EXEC

    The path to the raspbistill binary to use. Defaults to
    ``/usr/bin/raspistill``.

