"""set up file for module build"""
from setuptools import find_packages, setup

setup(
    name='ODIS',
    package_dir={"": "odis"},
    packages=find_packages(where="odis"),
    version='1.0.0',
    description='ODIS',
    author='Valeriu Morari',
    license='MIT',
)
