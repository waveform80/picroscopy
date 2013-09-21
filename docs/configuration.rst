.. _configuration:

=============
Configuration
=============

Picroscopy reads its configuration files from the following locations, in the
order presented (i.e. values found in later files override values found in
earlier files):

1. ``/etc/picroscopy.ini``

2. ``/usr/local/etc/picroscopy.ini``

3. ``~/.picroscopy.ini`` (where ``~`` represents the current user's home
   directory)

You can manually specify a configuration to load with the :option:`picroscopy
-c` option.  In this case, the manually specified configuration will be read
last, ensuring its values take precedence over any values read from the files
listed above.

Picroscopy's configuration format is based on the familiar `INI-file`_ format.
The configuration file must have a ``[picroscopy]`` section (Picroscopy will
ignore other sections within the file), which contains ``key=value`` entries on
separate lines. Key names are case insensitive.  Key names and values may have
leading or trailing whitespace which will be ignored.  Blank lines are ignored,
as are comments which are whole lines prefixed with either ``#`` or ``;``.

An example configuration file is shown below::

  [picroscopy]

  ; Blank lines are ignored, as is this line, which is a comment
  # This is also a comment

  ; Spaces surrounding keys and values are ignored...
    listen = 127.0.0.1:8000
  clients = 127.0.0.0/8

  ; Case is ignored for key names
  IMAGES_DIR=/tmp/picroscopy_images
  Thumbs_Dir=/tmp/picroscopy_thumbs

The key names which can appear in the configuration file are the same as the
available "long-style" command line options, with the caveat that leading
dashes are stripped and any dashes within the option are replaced by
underscore. Hence the :option:`picroscopy --images-dir` option becomes the
:ref:`images_dir` key within the configuration file.


Example Configurations
======================

Two example configuration files are shipped with Picroscopy's source:
``picroscopy.ini`` which contains a configuration suitable for normal usage
(all defaults), and ``development.ini`` which contains values suitable for
development purposes. It is recommended that ``picroscopy.ini`` be placed in a
suitable location where Picroscopy can find it automatically, e.g. ``/etc`` or
``/usr/local/etc``.


Keys
====

The remainder of this document is a description of the available keys in a
Picroscopy configuration file.


.. _log_file:

log_file
--------

Log displayed messages to the given filename. The log file will be appended to
if it already exists. Its format will include the timestamp that the message
was displayed, and the severity of the message. Log files include all messages
regardless of the verbosity of console output.


.. _pdb:

pdb
---

If ``true``, run under `PuDB`_ (if available) or PDB. This launches Picroscopy
within a Python debugger for development purposes.


.. _gstreamer:

gstreamer
---------

If ``true``, use a GStreamer pipeline instead of the ``raspivid`` or
``raspistill`` binaries to display the preview and capture images. This option
is intended to aid development on non-RPi platforms by permitting testing with
a webcam.


.. _listen:

listen
------

The address and port of the interface that Picroscopy will listen on.  Defaults
to ``0.0.0.0:80`` (when running as root) or ``0.0.0.0:8000`` (when running as a
non-root user). ``0.0.0.0`` address means "listen on all available network
interfaces".


.. _clients:

clients
-------

The network that clients must belong to. Clients that do not belong to the
specified network will be denied access to Picroscopy. Defaults to all valid
addresses (``0.0.0.0/0``).


.. _images_dir:

images_dir
----------

The directory in which Picroscopy will store images captured by the camera.  If
not specified, this defaults to a temporary directory which is destroyed upon
exit. If the specified directory does not exist, it will be created.


.. _thumbs_dir:

thumbs_dir
----------

The directory in which Picroscopy will store thumbnails generated from the
images taken by the camera. If not specified, defaults to a temporary directory
which is destroyed upon exit. If the specified directory does not exist, it
will be created. The thumbnails directory *must* be different to the images
directory.


.. _thumbs_size:

thumbs_size
-----------

The maximum size for generated thumbnails (the actual size may be smaller
due to aspect ratio preservation). Defaults to 320 pixels square.


.. _email_from:

email_from
----------

The address which Picroscopy will use as a From: address when sending e-mail.
The default is ``picroscopy`` with no specific host. If a host is not
specified, the configuration of the sending SMTP server will determine the host
associated with the address.


.. _sendmail:

sendmail
--------

Use the specified sendmail binary to send e-mail. This is the preferred option
for sending e-mail as it (usually) gracefully handles the case where the target
SMTP server is unavailable. Defaults to ``/usr/sbin/sendmail``.


.. _smtp_server:

smtp_server
-----------

Use the specified SMTP smarthost to send e-mail. This should only be used if
you do not wish to configure a local sendmail binary. If this option is
specified, it will always override any ``sendmail`` specification.


.. _raspivid:

raspivid
--------

The path to the raspivid binary to use. Defaults to ``/usr/bin/raspivid``.


.. _raspistill:

raspistill
----------

The path to the raspbistill binary to use. Defaults to ``/usr/bin/raspistill``.


.. _INI-file: http://en.wikipedia.org/wiki/INI_file
.. _PuDB: http://pypi.python.org/pypi/pudb
