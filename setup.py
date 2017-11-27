import os

from setuptools import find_packages, setup


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='RailgunS',
    version='0.8.0',
    install_requires=[
        'Django==2.0rc1',
        'djangorestframework',
        'djangorestframework-jwt',
        'djangorestframework-xml',
        'drf_openapi<=1.0.1',
        #
        'django-ckeditor',
        'django-crispy-forms',
        'django-extensions',
        'django-filter',
        'django-htmlmin',
        'itunes-iap',
        'mysqlclient',
        'pylibmc',
        'redis',
        #
        'djangorestframework-camel-case'
    ],
    dependency_links=[  # SO: https://stackoverflow.com/a/17442663/1823068,
        # 如果代码是0.9.9导致还是装的1.0.0时, 用pip --process-dependency-links解决
        'https://codeload.github.com/limdauto/drf_openapi/zip/master#egg=drf_openapi-1.0.1'
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
        'Framework :: Django :: 2.0rc1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
