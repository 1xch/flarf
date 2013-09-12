"""
Flarf: Flask Request Filter
-------------
Configurable request filters
"""

from setuptools import setup

setup(
    name='Flask-Flarf',
    version='0.0.5',
    url='https://github.com/thrisp/flarf',
    license='MIT',
    author='Thrisp/Hurrata',
    author_email='blueblank@gmail.com',
    description='Flask request filtering',
    long_description=__doc__,
    packages=['flask_flarf'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.9'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
