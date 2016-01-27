# Django questionnaire with InlineFormset

The application get with new aspect the most simple for questionnaire based on **InlineFormset**,
it is composed of two parts:

- Backend part, it's related to **admin** that can:
    - Create a questionnaire
    - Display the form of a questionnaire
    - Share the link of a questionnaire
    - Consult the statistics of a questionnaire

- Frontend part, it's related to **participant** that can :
    - Answer the questionnaire
    - Share via facebook, linkedin and google.

Here is some examples:

![examples](https://s3.amazonaws.com/questionnairedjango/survey/questionnairrr.jpg)

## Features

* based on nested inline formset
* participant has one attempt
* Question can be ordered by **drag and drop**
* Awesome template based on [materializecss](http://materializecss.com/)
* Not based on django Admin template
* Statistics with awesome displaying

Type of questions are:

    * Rating Scale
    * Yes or No
    * Multiple choice with one Answer
    * Multiple choice with multi answers
    * text field

## Install and setup
Create a new env for the project and switch to it


#!shell

> mkvirtualenv django_questionnaire

> workon django_questionnaire


Clone the repo with `git clone https://github.com/hamdigdoura/django-survey-formset.git`

After, run `pip install -r requirements.txt` and `python setup.py install`

Migrate  `python manage.py migrate`

Finally, Run the server `python manage.py runserver`


## Credits
For nested inline, i got from this [project](https://github.com/nyergler/nested-formset).
Thanks to [Nathan Yergler](https://github.com/nyergler)

## Contact Me
If you have any questions, comments or suggestion about `django questionnaire inline formset` ?
Hit me up at [Hamdi Gdoura](hamdigdouraisi@gmail.com)
