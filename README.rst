|python-versions| |github-build| |docs|

pyavb
=====

A python module for reading and writing Avid Bin Files (AVB) files.  Forked from https://github.com/markreidvfx/pyavb

Modified to include an ability to export AVB files to comma separated value (CSV)

Notice
------

This project is in no way affiliated, nor endorsed in any way with Avid, and their name and all product names are registered brand names and trademarks that belong to them.

Requirements
------------

- Python >= 2.7
- Ubuntu 22.04+

Installation
------------

clone the latest development git master::

    git clone https://github.com/rdamus/pyavb
    cd pyavb
    python setup.py install

Conda
~~~~~
I installed ``conda`` to manage the environment per `This guide <https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html>`_

Getting Started
---------------
Create a conda environment::

    conda create -n pyavb

Setup the ``PYTHON_PATH``::

    export PYTHONPATH=$PYTHONPATH:/path/to/pyavb/src:/path/to/pyavb/src/avb

Output AVB to CSV
-----------------

The following will produce a csv file of the avb input file, ``filename.avb``::

    pyavb/examples/python avb2csv.py filename.avb

The output CSV file will be produced in the same directory and is named ``data-YYYMMddTHHmmss.csv``

Documentation for pyavb
-------------

Documentation is available on `Read the Docs. <http://pyavb.readthedocs.io/>`_


.. |python-versions| image:: https://img.shields.io/badge/python-%3E%3D%202.7-blue.svg

.. |github-build| image:: https://github.com/markreidvfx/pyavb/actions/workflows/workflow.yml/badge.svg
    :alt: github actions
    :target: https://github.com/markreidvfx/pyavb/actions

.. |docs| image:: https://readthedocs.org/projects/pyavb/badge/?version=latest
    :alt: Documentation Status
    :target: http://pyavb.readthedocs.io/en/latest/?badge=latest
