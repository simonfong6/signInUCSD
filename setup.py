"""
setup.py
"""

from setuptools import setup

setup(
    name='signInUCSD',
    packages=['signInUCSD'],
    include_package_data=True,
    install_requires=[
        'flask',
        'pymongo',
        'bcrypt',
    ],
)
