# -*- coding: utf-8 -*-

from django.conf.urls import url

from .views import (CreateQuestionnaireView, TakeQuestionnaire,
                    UpdateQuestionnaireView, ThanksView,
                    ListQuestionnaireView, StatisticsQuestionnaireView)

urlpatterns = [

    # Displays the list of questionnaires (Bach-end User)
    url(r'^$',
        ListQuestionnaireView.as_view(),
        name='list-questionnaire'),

    # Creation of questionnaire (Back-end user)
    url(r'^create-questionnaire/$', CreateQuestionnaireView.as_view(),
        name='add-questionnaire'),

    # Updates and displays the questionnaire (Back-end User)
    url(r'create-questionnaire/(?P<pk>\d+)/$',
        UpdateQuestionnaireView.as_view(),
        name='update-questionnaire'),

    # Displays the statistics of questionnaire (Back-end User)
    url(r'create-questionnaire/(?P<pk>\d+)/statics/$',
        StatisticsQuestionnaireView.as_view(),
        name='statistics-questionnaire'),

    # Displays the questionnaire (Participant User)
    url(r'^take/(?P<pk>[0-9]+)/$',
        TakeQuestionnaire.as_view(),
        name='show-questionnaire'),

    # Thanks Message and sharing of the link of questionnaire
    #  (Both Back-end and Participant )
    url(r'^thanks/$',
        ThanksView.as_view(),
        name='thanks-page')
]
