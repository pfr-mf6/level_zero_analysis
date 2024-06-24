from setuptools import setup, find_packages

from pipeline.version import VERSION

setup(
    name='pipeline',
    version=VERSION,
    description='A command-line utility for data science',
    author='Micah Fullerton',
    author_email='micah.fullerton@portlandoregon.gov',
    url='<none yet>',
    packages=find_packages(),
    install_requires=[
        # List your app's dependencies here
        'docopt',
    ],
    classifiers=[
        # Choose classifiers from https://pypi.org/classifiers/
        # TODO:
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        'console_scripts': [
            'pipeline=main:main',
        ],
    },
)