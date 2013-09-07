.. _faq:

================================
Frequently Asked Questions (FAQ)
================================


Why can't I view the preview in the browser?
============================================

There are numerous reasons for choosing to use HDMI for the video preview. The
major one is simplicity: this was by far the quickest and simplest way of
getting the project working. It's also trivial for the user to setup, provides
perfect video quality and near-instant feedback of actions on the microscope.

Streaming over the LAN means dealing with encoding, client codecs, network
bandwidth, latency, the list goes on - and of course the result will never be
as good as the straight HDMI feed.

This is not to say that an in-browser preview isn't something that's being
considered for the future but it simply wasn't a priority for the first
version.


Why can't I control everything from the Pi?
===========================================

Again, simplicity. Building an application on the Pi that has an interface and
provides the live video interface means dealing with GPU coding (in order to
get reasonable preview quality and latency). Relying on a separate machine
running a web-browser to render the interface was the simplest method.

