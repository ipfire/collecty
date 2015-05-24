#!/bin/sh

libtoolize
intltoolize --force --automake
autoreconf --force --install --symlink
