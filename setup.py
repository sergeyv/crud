from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='crud',
      version=version,
      description="A SQLAlchemy/FormAlchemy automatic admin",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Sergey Volobuev',
      author_email='sergey.volobuev@gmail.com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      test_suite='crud',
      install_requires=[
          # -*- Extra requirements: -*-
        'SQLAlchemy',
        'FormAlchemy',
        'formish',
        #'repoze.bfg.formish',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
