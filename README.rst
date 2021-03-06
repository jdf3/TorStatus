TorStatus README
================

About TorStatus
---------------
TorStatus provides a way for Tor relay operators, clients of the Tor
network, and anyone else to view aggregate information about the Tor
network as well as detailed information about active relays in the
network in real-time.

This implementation is written in Python/Django.

Installation
------------
For help installing and running TorStatus, consult ``doc/INSTALL.rst``.

Documentation
-------------

Files
.....
In ``TorStatus/``:

    | ``README.rst`` -- This document.

In ``TorStatus/doc``:

    | ``DESIGN.rst`` -- Design documentation and issues.
    | ``INSTALL.rst`` -- Installation instructions.
    | ``HACKING`` -- Coding style guidelines used for TorStatus.
    | ``LICENSE`` -- A copy of the BSD 3-clause license that TorStatus
                     uses.

Generating the API
..................
To generate the TorStatus API, install epydoc (available at
http://epydoc.sourceforge.net/installing.html) and run:

    | ``$ cd status/``
    | ``$ epydoc . --config config/epydoc_config.py``

ReStructured Text
.................
TorStatus documentation, like this ``README``, is written in
reStructuredText. To generate HTML-formatted design documentation using
reStructuredText, install docutils (available at
http://docutils.sourceforge.net/) and run commands analogous to
the following:

    | ``$ cd doc/``
    | ``$ rst2html example.rst example.html``

To view the documentation, open ``design.html`` using your favorite web
browser. If you'd rather view the plaintext documentation, open
``design.rst``.
