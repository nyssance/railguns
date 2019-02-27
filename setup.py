import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='RailgunS',
    version='0.10.0',
    install_requires=[
        'django[argon2]==2.2b1',
        'djangorestframework',
        'djangorestframework-jwt',
        'drf-yasg[validation]',
        'stringcase',
        #
        'django-ckeditor',
        'django-crispy-forms',
        'django-extensions',
        'django-filter',
        'django-htmlmin',
        'django-redis',
        'itunes-iap',
        'mysqlclient'
    ],
    extras_require={
        'dev': ['django-haystack-panel', 'django-rosetta', 'markdown', 'pygments'],
        'prod': []
    },
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='Only My Railgun',
    long_description=README,
    url='https://github.com/nyssance/railguns',
    author='NY',
    author_email='nyssance@icloud.com',
    classifiers=[
        #
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ])
