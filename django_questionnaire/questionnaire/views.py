# -*- coding: utf-8 -*-

from django.contrib.messages import success, error
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import (CreateView, FormView,
                                  UpdateView, TemplateView,
                                  ListView)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from .forms import (QuestionnaireForm, DisplayQuestionsForm,
                    QuestionFormSet)
from .models import Questionnaire


class QuestionnaireMixin(object):
    model = Questionnaire
    form_class = QuestionnaireForm
    template_name = 'questionnaire/create.html'

    def form_valid(self, form):
        context = self.get_context_data()
        question_form = context['question_formset']
        if question_form.is_valid():
            question_form.instance = self.object = form.save()
            question_form.save()
            success(self.request, _("All updates has been saved successfully."))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(QuestionnaireMixin, self).get_context_data(**kwargs)
        help_text_msg = [{'help_text': 'This field is required'}, ]
        if self.request.POST:
            context['question_formset'] = QuestionFormSet(self.request.POST,
                                                          instance=self.object,
                                                          initial=help_text_msg
                                                          )
        else:
            context['question_formset'] = QuestionFormSet(instance=self.object,
                                                          initial=help_text_msg
                                                          )
        return context


class ListQuestionnaireView(ListView):
    model = Questionnaire
    template_name = "questionnaire/list.html"

    def get_context_data(self, **kwargs):
        context = super(ListQuestionnaireView, self).get_context_data(**kwargs)
        context['questionnaires'] = Questionnaire.objects.order_by('id')
        return context


class CreateQuestionnaireView(QuestionnaireMixin, CreateView):

    def get_success_url(self):
        return reverse('update-questionnaire', kwargs={'pk': self.object.id})


class UpdateQuestionnaireView(QuestionnaireMixin, UpdateView):

    def get_initial(self):
        return {'pk': self.kwargs['pk']}

    def get_success_url(self):
        return reverse('update-questionnaire', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super(UpdateQuestionnaireView, self).get_context_data()
        context['display_questions'] =\
            DisplayQuestionsForm(questionnaire_id=self.kwargs['pk'])
        return context


class StatisticsQuestionnaireView(TemplateView):
    template_name = 'questionnaire/statistics.html'

    def get_queryset(self):
        return get_object_or_404(Questionnaire, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(StatisticsQuestionnaireView, self).get_context_data(**kwargs)
        q = self.get_queryset()
        context['questionnaire'] = q.questions()
        context['statistics'] = q.question_set.calculate_statistics_all()
        return context


class TakeQuestionnaire(FormView):
    form_class = DisplayQuestionsForm
    template_name = 'questionnaire/display.html'

    def get_form_kwargs(self):
        kwargs = super(TakeQuestionnaire, self).get_form_kwargs()
        kwargs.update({'questionnaire_id': self.kwargs['pk']})
        return kwargs

    def get_success_url(self):
        return reverse('thanks-page')

    def form_valid(self, form):
        error_integrity = form.save(user=self.request.user)
        if error_integrity:
            error(self.request, "Your not allowed to response more than one.")
            return self.render_to_response(self.get_context_data(form=form))

        return super(TakeQuestionnaire, self).form_valid(form=form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TakeQuestionnaire, self).dispatch(*args, **kwargs)


class ThanksView(TemplateView):
    template_name = "questionnaire/thanks.html"

    def get_context_data(self, **kwargs):
        context = super(ThanksView, self).get_context_data(**kwargs)

        if 'url' in self.request.GET:
            context['url_questionnaire'] = "%s%s" % (self.request.META['HTTP_HOST'],
                                                     self.request.GET['url'])
        return context
