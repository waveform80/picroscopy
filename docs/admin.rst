.. _admin:

====================
Administrators Guide
====================

This section of the manual deals with configuring Picroscopy either via the
command line switches or via a configuration file specified on the command
line. It also provides rudimentary guidance on configuration of the `Raspbian`_
operating system under the assumption that this is the operating system most
users will be using for Picroscopy.

  .. note:: If any users wish to use Picroscopy with `Arch Linux`_ (the other
    major distro available for the Raspberry Pi platform), please feel free to
    submit documentation patches to the author.


.. _networking:

Network configuration
=====================

The ``/etc/network/interfaces`` file holds the network configuration under
Raspbian. The default configuration which is shown below, attempts to obtain an
IP address via DHCP::

    iface eth0 inet dhcp

Should you wish your Pi to use a static address you will need to edit this
file. A typical static address configuration for the private 10.0.0.0 network
is shown below::

    iface eth0 inet static
        address 10.0.0.150
        netmask 255.0.0.0
        gateway 10.0.0.1

Another static configuration is shown below, this time for the private
192.168.0.0 network typically used by home routers::

    iface eth0 inet static
        address 192.168.1.3
        netmask 255.255.255.0
        gateway 192.168.1.1

After changing ``/etc/network/interfaces`` you will need to restart the
networking service for the changes to take effect (note that if you are
connected to your Pi via SSH this will very likely break your session)::

    $ sudo service networking restart

Alternatively you can simply reboot::

    $ sudo reboot


.. _command_line:

Command Line
============

Picroscopy is started from the command line with the ``picroscopy`` command.
Typically, options for the application are either passed as command line
switches, or are specified as entries in a configuration file which is
specified with the :option:`picroscopy -c` option. If an option appears both
in the configuration file and as a switch on the command line, the command
line switch will take precedence. Specifically, the order of precedence for
options is:

1. command line switch

2. configuration key

3. default

The Picroscopy application does not fork like a daemon once started. As it is
a single user application that utilizes the Raspberry Pi's display there is
little point in running as a system daemon.


.. _config:

Configuration Files
===================


.. _Arch Linux: http://archlinuxarm.org/platforms/armv6/raspberry-pi
.. _Raspbian: http://www.raspbian.org/
