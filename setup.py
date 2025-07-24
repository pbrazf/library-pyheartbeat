from setuptools import setup, find_packages
import io

version = '0.0.10'
readme = io.open('README.md', encoding='utf-8').read()

setup(name='pyheartbeat',
    version=version,
    license='MIT License',
    author='Pedro Ferreira Braz',
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email='pbraz.pedrof@gmail.com',
    keywords='pyheartbeat, heartbeat_library, heartbeat, heartbeat-library, heartbeat-api, heartbeat-wrapper, heartbeat-python, heartbeat-python-wrapper, heartbeat-python-api, heartbeat-python-wrapper-api, heartbeat-python-api-wrapper, multithreading, threading, requests, python-requests, python-threading, python-multithreading, python-heartbeat, python-heartbeat-api, python-heartbeat-wrapper, python-heartbeat-python, python-heartbeat-python-wrapper, python-heartbeat-python-api, python-heartbeat-python-wrapper-api, python-heartbeat-python-api-wrapper',
    description=u'Library for sending pulses to a process monitoring server',
    packages=find_packages(),
    install_requires=[
        'requests',
        'apscheduler'
    ])
