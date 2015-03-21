from setuptools import setup, find_packages

setup(
name="rtstat",
version='0.1.0',
scripts=['rtstat/rtstat.py'],
entry_points = {'console_scripts': ['rtstat = rtstat:main']},
url='https://github.com/TomCrypto/rtstat',
license='MIT',
description=
"Tool that extracts information from routers via " +
"telnet for later use e.g. monitoring. Mostly for " +
"personal use, but still extensible. Python 3 only.",
author='Thomas BENETEAU',
author_email='thomas.beneteau@yahoo.fr',
packages=find_packages(),
classifiers=[
'Programming Language :: Python :: 3',
'Topic :: Terminals :: Telnet',
'Topic :: System :: Networking :: Monitoring',
'Topic :: Internet :: Log Analysis',
],
)
