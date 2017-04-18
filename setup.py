import os

from setuptools import find_packages, setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='railguns',
    version='0.1.9',
    install_requires=[
        'Django',
        'djangorestframework',
        'djangorestframework-jwt',
        'djangorestframework-xml',
        'django-rest-swagger',
        #
        'django-ckeditor',
        'django-filter',
        'django-htmlmin',
        'itunes-iap',
        'mysqlclient',
        'pylibmc',
        'redis',
        #
        'djangorestframework-camel-case'
    ],
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    description='Only My Railgun',
    long_description=README,
    url='https://github.com/nypisces/railguns',
    author='NY',
    author_email='nypisces@live.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)
