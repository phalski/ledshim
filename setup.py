from setuptools import setup

setup(
    name='phalski-ledshim',
    version='0.1.0',
    packages=['phalski_ledshim', 'phalski_ledshim.animation', 'phalski_ledshim.charting', 'phalski_ledshim.threading'],
    url='https://github.com/phalski/phalski-ledshim',
    license='MIT',
    author='phalski',
    author_email='mail@phalski.com',
    description='A basic application framework for the Pimoroni LED SHIM',
    install_requires=[
        'ledshim==0.0.1'
    ]
)
