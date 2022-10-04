#!/bin/bash

# Build source distribution
python setup.py sdist

# Move the distro file to pypi server
mv dist/*.tar.gz /packages
