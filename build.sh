#!/bin/bash
cd $HOME/pgdb
$PYTHON setup.py build
$PYTHON setup.py sdist
$PYTHON setup.py install
