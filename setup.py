from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='phalski-ledshim',
    version='0.2.0',
    packages=['phalski_ledshim'],
    url='https://github.com/phalski/phalski-ledshim',
    author='phalski',
    author_email='mail@phalski.com',
    description='A basic application framework for the Pimoroni LED SHIM',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'ledshim>=0.0.1'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
