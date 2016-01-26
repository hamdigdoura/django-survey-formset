# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (Questionnaire, Question,
                     Choice, Answer)


class AnswerAdmin(admin.ModelAdmin):
    list_filter = ('user', )

admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Answer, AnswerAdmin)
