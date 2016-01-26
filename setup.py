import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django_survey_formset',
    version='0.0.1',
    packages=['django_questionnaire', 'django_questionnaire.config',
              'django_questionnaire.questionnaire',
              'django_questionnaire.questionnaire.migrations',
              'django_questionnaire.questionnaire.templatetags'],
    author='Hamdi Gdoura',
    author_email='hamdigdouraisi@gmail.com',
    description='Django survey',
    long_description=read('README.md'),
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    keywords=['questionnaire', 'nested inline formset', 'survey'],
    url='https://github.com/hamdigdoura/django-survey-formset.git',
    license='MIT License',
    install_requires=[
        'Django>=1.9',
        ],
)
