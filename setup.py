"""

Project: ApiToolbox

File Name: setup.py

Author: Zachary Romer, zach@scharp.org

Creation Date: 7/13/19

Version: 1.0

Purpose:

Special Notes:

"""
import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='ApiToolbox',
    version='0.0.1',
    author='zromer@fredhutch.org',
    description='Provides basic tools for quickly implementing RESTful APIs in Flask',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sciscogenetics/ApiToolbox',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
