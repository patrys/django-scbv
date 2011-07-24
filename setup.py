#! /usr/bin/env python
from setuptools import setup, find_packages

version = __import__('scbv').get_version()

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

PACKAGE_DATA = {
    '': [
        'templates/*.*',
        'templates/**/*.*',
    ],
}

REQUIREMENTS = [
    'django >= 1.3',
]

EXTRAS = {}

setup(name='django-scbv',
      author='Patryk Zawadzki',
      author_email='patrys@gmail.com',
      description='Simple (and sane) class-based views for Django',
      version = version,
      packages = find_packages(),
      package_data=PACKAGE_DATA,
      classifiers=CLASSIFIERS,
      install_requires=REQUIREMENTS,
      extras_require=EXTRAS,
      platforms=['any'],
      zip_safe=False)
