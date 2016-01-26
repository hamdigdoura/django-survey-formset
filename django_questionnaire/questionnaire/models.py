# -*- coding: utf-8 -*-
from __future__ import division
from __builtin__ import enumerate

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

import datetime
import itertools


class Questionnaire(models.Model):
    title = models.CharField(verbose_name=_('Questionnaire title'),
                             max_length=200,
                             help_text=_('Note: Name of the questionnaires'),
                             )
    description = models.TextField(verbose_name=_('Description'),
                                   blank=True,
                                   help_text=_('Enter the text that presents '
                                               'the questionnaire'),
                                   )

    def __unicode__(self):
        return self.title

    def questions(self):
        return self.question_set.all().order_by('order')

    def number_responses(self):
        return Answer.objects \
            .filter(question__questionnaire=self.id) \
            .distinct('user').count()


class QuestionQuerySet(models.QuerySet):
    def _filter_choices_by_dates(self, result_query):
        date_list = []
        count_query = []
        # Grouped the choices by dates
        grouped = itertools.groupby(result_query, lambda recorded: recorded.get('date'))
        for date, query_by_day in grouped:
            # List of date choices
            date_list.append(date)
            # List of count choices
            count_query.append(len(list(query_by_day)))
        return [date_list, count_query]

    def _fill_dates_with_zero(self, all_dates, question_list):
        dates_str_list = []
        # Contain all dates and delete the duplication of date
        no_duplication_dates = list(set(all_dates))
        # Get the max and the min date
        dates_max_min_list = [min(no_duplication_dates), max(no_duplication_dates)] if no_duplication_dates !=[] else []
        # Fills the dates between the min and max date
        date_compare = int((max(no_duplication_dates) - min(no_duplication_dates)).days) if no_duplication_dates !=[] else 0
        if date_compare > 1:
            for i in xrange(1, date_compare):
                val = (no_duplication_dates[0] + datetime.timedelta(days=i))
                dates_max_min_list.insert(i, val)

        # question_list: [List date, count choices, text choice
        # Add the count of choices if date of choice in list dates else add zero
        for i, filtered in enumerate(question_list):
            list_choice = []
            for date in dates_max_min_list:
                item_list = 0
                if date in filtered[0]:
                    index = filtered[0].index(date)
                    item_list = filtered[1][index]
                list_choice.append(item_list)
            question_list[i] = list_choice
        # change the form of date to string "day month year"
        for date in dates_max_min_list:
            dates_str_list.append(date.strftime('%b %d %Y'))
        return question_list, dates_str_list

    def _reformat_dict_static(self, choice_question_list, question_list,
                              dates_str_list, result):
        # Reformat the dict
        choice_dict = {}
        old_choice = 0
        for index, choice in enumerate(choice_question_list):
            if choice[1] == old_choice:
                choice_dict.update({
                    choice[0]: question_list[index]
                })
            else:
                choice_dict = {
                    choice[0]: question_list[index]
                }
            result[choice[1]].update({
                'choices': choice_dict,
                'dates': dates_str_list
            })
            old_choice = choice[1]
        return result

    def _get_statistics_multichoice(self, query_multi_choice):
        result = {}
        question_list = []
        all_dates = []
        choice_question_list = []
        # Get the question of type multi-choice
        for question in query_multi_choice:
            question_result = {}
            # Get the choices
            for choice in question.choices():
                q = question.answer_set.answers_multiple_choice(choice.text)
                # encode the text choice
                choice_text_str = choice.text.encode('utf-8')
                # Text choice list composition[choice_text, question_id ]
                choice_question_list.append([choice_text_str, question.id])
                question_result[choice_text_str+'_count'] = q.count()
                choices_dates_list = self._filter_choices_by_dates(q
                                                                   .values('date')
                                                                   .order_by('date'))
                # List [date, count_choices]
                question_list.append(choices_dates_list)
                # List of all dates
                all_dates += choices_dates_list[0]
            question_result["total"] = question.answer_set.count()
            result[question.id] = question_result
        question_list, dates_str_list = self._fill_dates_with_zero(all_dates,
                                                                   question_list
                                                                   )
        return self._reformat_dict_static(choice_question_list,
                                          question_list,
                                          dates_str_list,
                                          result)

    def types_yes_no(self):
        return self.filter(type='yesNoQuestion')

    def types_multi_choices_one_answer(self):
        return self.filter(type='MultiChoices')

    def types_multi_choices_multi_answers(self):
        return self.filter(type='MultiChoiceWithAnswer')

    def types_rating(self):
        return self.filter(type='RatingField')

    def types_text(self):
        return self.filter(type='TextField')

    def calculate_statistics_yes_no(self):
        result = {}
        for question in self.types_yes_no():
            rslt = {}
            val = 0
            answers = question.answer_set
            rslt['yes_count'] = answers.answers_yes().count()
            rslt['no_count'] = answers.answers_no().count()
            rslt['total'] = answers.count()
            try:
                rslt['percent_no'] = round(((rslt['no_count']) / rslt['total'])*100, 1)
                # if the question is not required, maybe some participants are not
                # responding to it.
                rslt['percent_yes'] = round(((rslt['yes_count']) / rslt['total'])*100, 1)
                rslt['percent_other'] = round(100-(rslt['percent_yes']+rslt['percent_no']), 1)

            except ZeroDivisionError:
                rslt['percent_no'] = 0
                rslt['percent_yes'] = 0
                rslt['total'] = 0
                rslt['percent_other'] = 0

            result[question.id] = rslt
        return result

    def calculate_statistics_multi_choices_one_answer(self):
        return self._get_statistics_multichoice(
            self.types_multi_choices_one_answer()
        )

    def calculate_statistics_multi_choices_multi_answers(self):
        return self._get_statistics_multichoice(
            self.types_multi_choices_multi_answers()
        )

    def calculate_statistics_rating(self):
        # Bars and total satisfaction in Pie
        result = {}
        for question in self.types_rating():
            rslt = {}
            total = 0
            for answer in question.answer_set.answers_rating():
                total += float(((answer.answer)).encode('utf-8'))
            try:
                rslt['satisfaction_total'] = round((float(total / (question.answer_set.answers_rating().count() * 5)))*100, 1)
            except ZeroDivisionError:
                rslt['satisfaction_total'] = 0
            rslt['total'] = question.answer_set.answers_rating().count()
            rslt['poor_count'] = question.answer_set.answers_rating_poor().count()
            rslt['ok_count'] = question.answer_set.answers_rating_ok().count()
            rslt['good_count'] = question.answer_set.answers_rating_good().count()
            if not question.required:
                rslt['not_responding'] = question.answer_set.count() - (rslt['poor_count']
                                                                        + rslt['ok_count']
                                                                        + rslt['good_count']
                                                                        )
            result[question.id] = rslt

        return result

    def calculate_statistics_text(self):
        result = {}
        for question in self.types_text():
            rst = []
            for answer in question.answer_set.all():
                rst.append([answer.user, (answer.answer).encode('utf-8').replace('"', '')])
            result[question.id] = rst
        return result

    def calculate_statistics_all(self):
        result = {}
        for statistics_dict in (self.calculate_statistics_multi_choices_multi_answers(),
                                self.calculate_statistics_multi_choices_one_answer(),
                                self.calculate_statistics_rating(),
                                self.calculate_statistics_text(),
                                self.calculate_statistics_yes_no()):
            result.update(statistics_dict)
        return result


class Question(models.Model):
    CHOICES = (('yesNoQuestion',
                _('Yes/No'),
                _('The participant must respond with Yes or No.')
                ),

               ('MultiChoices',
                _('Multiple choices with one Answer'),
                _('The participant is conducted to pick one in response'
                  ' options list.'),
                ),

               ('MultiChoiceWithAnswer',
                _('Multiple choices with multiple answers'),
                _('The participant is conducted to pick (one or more '
                  'responses) in response options list.'),
                ),

               ('TextField',
                _('Comment Area'),
                _('Use the comment box to collect written comments from'
                  ' respondents.')),

               ('RatingField',
                _('Rating scale'),
                _('The respondents will rate the level of satisfaction.')),
               )

    TYPE_CHOICES = tuple((key,
                          mark_safe(u'<span class="black-text">%s</span>'
                                    u'<br><small class="teal-text">%s</small>' %
                                    (label, help_text)))
                         for key, label, help_text in CHOICES)

    text = models.TextField(verbose_name=_('Title Question'),
                            max_length=100,
                            help_text=_('Note: Title of question'))

    required = models.BooleanField(verbose_name=_('Question Required'),
                                   default=True,
                                   help_text=_('The users are required to answer'),
                                   )
    questionnaire = models.ForeignKey(Questionnaire)
    type = models.CharField(verbose_name=_('Type of answer'),
                            max_length=200,
                            blank=False,
                            default=TYPE_CHOICES[0][0],
                            choices=TYPE_CHOICES,
                            )
    order = models.IntegerField(verbose_name=_("order"),
                                default=0)
    help_text = models.TextField(verbose_name=_('Help Text'),
                                 blank=True,
                                 )
    objects = QuestionQuerySet.as_manager()

    def __unicode__(self):
        return u'Qstaire-%s-Qustion-%s' % (self.questionnaire.title,
                                           self.id)

    def choices(self):
        choice_list = self.choice_set.all()
        return choice_list

    def answers(self):
        answer_list = self.answer_set.all()
        return answer_list

    class Meta:
        ordering = ['order', ]


class Choice(models.Model):
    question = models.ForeignKey(Question)
    text = models.CharField(verbose_name=_('Text choice'),
                            max_length=200,
                            )

    def __unicode__(self):
        return u'Qsaire-%s-Qst-%s-Ch-%s' % (self.question.questionnaire.title,
                                            self.question.id,
                                            self.id)


class AnswerQuerySet(models.QuerySet):
    def answers_yes(self):
        return self.filter(answer='"yes"')

    def answers_no(self):
        return self.filter(answer='"no"')

    def answers_rating(self):
        return self.filter(answer__range=(0, 5))

    def answers_rating_poor(self):
        # Between 0% and 40%
        return self.filter(answer__range=(0, 2))

    def answers_rating_ok(self):
        # Between 40% and 60%
        return self.filter(answer__range=(2, 3))

    def answers_rating_good(self):
        # Between 60% and 100%
        return self.filter(answer__range=(3, 5))

    def answers_multiple_choice(self, choice):
        return self.filter(answer__contains="%s" % choice)


class Answer(models.Model):
    user = models.ForeignKey(User,
                             help_text=_('The user who supplied this answer'),
                             )
    question = models.ForeignKey(Question,
                                 help_text=_('The question that this is an answer to'),
                                 )
    answer = JSONField(verbose_name=_('Answer'),
                       blank=True,
                       help_text=_('The text answer related to the question'),
                       )
    date = models.DateField(verbose_name=_("Date"),
                            default=datetime.date.today)

    objects = AnswerQuerySet.as_manager()

    def __unicode__(self):
        return u'Qsaire-%s-Qst-%s-Ans-%s' % (self.question.questionnaire.title,
                                             self.question.id,
                                             self.id)

    class Meta:
        unique_together = ('user', 'question')
