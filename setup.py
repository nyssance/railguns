from setuptools import find_packages, setup


with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='RailgunS',
    version='0.81',
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
        'Framework :: Django :: 5.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP'
    ],
    # package_dir={'': 'src'},
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.12',
    # zip_safe=False,
    include_package_data=True,
    install_requires=[
        'django[argon2]==5.0.2',
        'djangorestframework==3.14.0',
        'djangorestframework_simplejwt==5.3.0',
        'gunicorn==21.2.0',
        'uvicorn==0.23.2',
        #
        'django-ckeditor==6.7.0',
        'django-filter==23.2',
        'django-htmlmin==0.11.0',
        'hiredis==2.2.3',
        'mysqlclient==2.2.4',
        'redis==5.0.1'
    ],
    extras_require={
        'dev': [],
        'prod': []
    }
)
