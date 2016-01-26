# -*- coding: utf-8 -*-

from django import forms
from django.db import IntegrityError
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from .models import (Questionnaire, Question,
                     Choice, Answer)

import json


class BaseNestedFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseNestedFormset, self).__init__(*args, **kwargs)
        # The empty questionnaire was not permitted
        for form in self.forms:
            form.empty_permitted = False

    def clean(self):
        """
        Forms must have at least:
                        - One question (update questionnaire)
                        - Two choices (create and update questionnaire)
        :return Handle Attribute Error or Clean data
        """
        min_num_question = 1
        min_num_choice = 2
        if self.total_form_count() >= min_num_question and \
                (self.total_form_count() == len(self.deleted_forms)):
            raise forms.ValidationError("You must have at least one question")
        else:
            multiple_choice_type_list = ['MultiChoices',
                                         'MultiChoiceWithAnswer'
                                         ]

            for index, form in enumerate(self.forms):
                inline_items = []
                if hasattr(form.nested, 'cleaned_data'):
                    for choice in form.nested.cleaned_data:
                        if choice.get('text', None) \
                                and not choice.get('DELETE', None):
                            inline_items.append(choice.get('text'))
                    if len(inline_items) < min_num_choice \
                            and form.cleaned_data['type'] \
                                    in multiple_choice_type_list:
                        form.errors['choice'] = _("You must entered at least two"
                                                  " choices")

        return super(BaseNestedFormset, self).clean()

    def add_fields(self, form, index):
        super(BaseNestedFormset, self).add_fields(form, index)
        form.nested = self.nested_formset_class(
            instance=form.instance,
            data=form.data if self.is_bound and index is not None else None,
            prefix='%s-%s' % (
                form.prefix,
                self.nested_formset_class.get_default_prefix(),
            ),
        )

    def is_valid(self):
        result = super(BaseNestedFormset, self).is_valid()
        if self.is_bound:
            for form in self.forms:
                result = result and form.nested.is_valid()
        return result

    def save(self, commit=True):
        result = super(BaseNestedFormset, self).save(commit=commit)
        choice_empty = ['yesNoQuestion', 'TextField', 'RatingField']
        for form in self.ordered_forms:
            # Save the order of the form
            form.instance.order = \
                form.cleaned_data['ORDER']\
                    if form.cleaned_data['ORDER'] is not None \
                    else self.total_form_count()
            # Delete question when type of question `choice_empty`
            if form.cleaned_data['type'] in choice_empty:
                form.nested.save(commit=False)
                for choice in form.nested:
                    if choice.instance.pk:
                        choice.instance.delete()
            else:
                form.nested.save(commit=commit)
            form.instance.save()

        return result


def nested_formset_factory(parent_model, child_model, grandchild_model):
    parent_child = inlineformset_factory(
        parent_model,
        child_model,
        formset=BaseNestedFormset,
        max_num=1,
        fields="__all__",
        widgets={'type': forms.RadioSelect(),
                 'text': forms.Textarea({'class': 'materialize-textarea'})
                 },
        extra=1,
        exclude=['help_text', 'order', ],
        can_order=True,
        can_delete=True,
    )

    parent_child.nested_formset_class = inlineformset_factory(
        child_model,
        grandchild_model,
        max_num=8,
        extra=4,
        validate_max=True,
        widgets={'text': forms.TextInput()},
        exclude=['ORDER', ],
        can_delete=True,
    )

    return parent_child

# The best link: http://yergler.net/blog/2009/09/27/nested-formsets-with-django/
# Nested formset
QuestionFormSet = nested_formset_factory(Questionnaire,
                                         Question,
                                         Choice,
                                         )


class QuestionnaireForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionnaireForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Questionnaire
        fields = "__all__"
        widgets = {
            'title': forms.TextInput(),
            'description': forms.Textarea({'class': 'materialize-textarea'}),
            }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"
        widgets = {
            'text': forms.Textarea(),
            'type': forms.RadioSelect(),
            }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = "__all__"


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = "__all__"


class DisplayQuestionsForm(forms.Form):
    def __init__(self, questionnaire_id, *args, **kwargs):
        """
        Get list of questions and generate the form related to each question's type
        :param questionnaire_id: Id questionnaire
        """
        super(DisplayQuestionsForm, self).__init__(*args, **kwargs)
        self.questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
        for index, question in enumerate(self.questionnaire.questions()):
            options = {
                'required': question.required,
                'label': question.text,
                }

            if question.required:
                options.update({'help_text': question.help_text})

            choices_text = Question.objects\
                .get(id=question.id)\
                .choices()\
                .values_list('text', 'text')

            if question.type == 'yesNoQuestion':
                choices_yes_no = (("yes", _("Yes")),
                                  ("no", _("No")),)

                error_message = {"required": "This field is required and your"
                                             " response must be yes or no"}

                self.fields['question_{0}'.format(index)] \
                    = forms.ChoiceField(choices=choices_yes_no,
                                        widget=forms.RadioSelect({'class': 'with-gap'}),
                                        error_messages=error_message,
                                        **options)

            elif question.type == 'TextField':
                message_error = {"required": "This field is required and you"
                                             " must enter your text"}

                self.fields['question_{0}'.format(index)] = \
                    forms.CharField(widget=forms.Textarea({'class':
                                                               'materialize-textarea'}),
                                    error_messages=message_error,
                                    **options)

            elif question.type == 'MultiChoiceWithAnswer':

                error_message = {'required': "This field is required and you"
                                             " must select responses"}

                self.fields['question_{0}'.format(index)] = \
                    forms.MultipleChoiceField(
                        choices=choices_text,
                        widget=forms.CheckboxSelectMultiple,
                        error_messages=error_message,
                        **options)

            elif question.type == 'MultiChoices':
                error_message = {'required': "This field is required and you "
                                             "must select a response"}

                self.fields['question_{0}'.format(index)] = \
                    forms.ChoiceField(
                        choices=choices_text,
                        widget=forms.RadioSelect({'class': 'with-gap'}),
                        error_messages=error_message,
                        **options)

            elif question.type == 'RatingField':
                self.fields['question_{0}'.format(index)] = \
                    forms.IntegerField(
                        max_value=5,
                        min_value=0,
                        **options
                    )
                self.fields[
                    'question_{0}'.format(index)
                ].widget.attrs.update({'class': "rating",
                                       'data-min': "0",
                                       'data-max': "5",
                                       'data-step': "1",
                                       'data-glyphicon': "false",
                                       'data-size': "sm",
                                       'data-stars': 5})

    def save(self, user):
        for index, question in enumerate(self.questionnaire.questions()):
            answer_text = self.cleaned_data['question_{0}'.format(index)]
            if answer_text:
                answer = json.dumps(answer_text)
                try:
                    answer_save = Answer(user=user,
                                         question=question,
                                         answer=answer)
                    answer_save.save()
                except IntegrityError:
                    error_integrity = True
                    return error_integrity