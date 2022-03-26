from setuptools import find_packages, setup


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='RailgunS',
    version='0.56',
    author='NY',
    author_email='nyssance@icloud.com',
    description='Only My Railgun',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nyssance/railguns',
    project_urls={
        'Bug Tracker': 'https://github.com/nyssance/railguns/issues'
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP'
    ],
    # package_dir={'': 'src'},
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.10',
    # zip_safe=False,
    include_package_data=True,
    install_requires=[
        'django[argon2]==4.0.3',
        'djangorestframework==3.13.1',
        'djangorestframework_simplejwt==5.1.0',
        'gunicorn==20.1.0',
        'uvicorn==0.17.6',
        #
        'django-ckeditor==6.2.0',
        'django-filter==21.1',
        'django-htmlmin==0.11.0',
        'hiredis==2.0.0',
        'mysqlclient==2.1.0',
        'redis==4.2.0'
    ],
    extras_require={
        'dev': [],
        'prod': []
    }
)
