import os

from setuptools import find_packages, setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='RailgunS',
    version='0.51',
    url='https://github.com/nyssance/railguns',
    author='NY',
    author_email='nyssance@icloud.com',
    description='Only My Railgun',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'django[argon2]==4.0',
        'djangorestframework==3.13.1',
        'djangorestframework_simplejwt==5.0.0',
        'gunicorn==20.1.0',
        'uvicorn==0.16.0',
        #
        'django-ckeditor==6.2.0',
        'django-filter==21.1',
        'django-htmlmin==0.11.0',
        'hiredis==2.0.0',
        'mysqlclient==2.1.0',
        'redis==4.0.2'
    ],
    extras_require={
        'dev': [],
        'prod': []
    },
    python_requires='>=3.10',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP'
    ],
    project_urls={'Source': 'https://github.com/nyssance/railguns'})
