from django.test import Client, TestCase
from rebar.testing import flatten_to_dict

from .models import Questionnaire, Question, User, Choice, Answer
from .forms import QuestionFormSet, DisplayQuestionsForm


class CreateQuestionnaireTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.questionnaire = Questionnaire.objects.create(title='questionnaire test',
                                                          description='test')
        self.user = User.objects.create_user(username='test',
                                             email='test@test.tn',
                                             password='test0000')

        self.user.is_staff = self.user.is_superuser = False
        self.user.is_active = True
        self.user.save()

    def get_form_data(self, formset):
        """
        Get from Formset the data field
        :param formset:
        :return:
        """
        form_data = flatten_to_dict(formset)
        for form in formset:
            form_data.update(
                flatten_to_dict(form.nested)
            )

        return form_data

    def test_add_question_type_yes_no(self):
        unbound_form = QuestionFormSet(instance=self.questionnaire)
        # Verify form if question and choice are empty
        self.assertFalse(unbound_form.is_valid())
        # Get the fields of QuestionFormset
        form_data = self.get_form_data(unbound_form)
        # Adds some data
        form_data.update({
            'question_set-0-text': 'text test0',
            'question_set-0-type': 'yesNoQuestion',
            })

        form_question = QuestionFormSet(
            instance=self.questionnaire,
            data=form_data,
        )
        # Verify form
        self.assertTrue(form_question.is_valid())

        form_question.save()
        # verify the data storing
        self.assertEqual(
            Question.objects.get(questionnaire=self.questionnaire.id).type,
            'yesNoQuestion',
        )
        # Add a new choice when type of question `yesNoQuestion`
        form_data.update({
            'question_set-0-choice_set-0-text': 'choice test 0',
            })
        form_question = QuestionFormSet(
            instance=self.questionnaire,
            data=form_data,
        )
        # Verify if the form is valid
        self.assertTrue(form_question.is_valid())
        form_question.save()

        question = Question.objects.filter(questionnaire=self.questionnaire.id,
                                           type='yesNoQuestion')[0]

        # verify non-storage of choice when question's type `yesNoQuestion`
        self.assertEqual(
            Choice.objects.filter(question=question.id).count(), 0)

    def test_add_question_type_multichoices(self):
        unbound_form = QuestionFormSet(instance=self.questionnaire)
        # Verify form if question and choice are empty
        self.assertFalse(unbound_form.is_valid())

        # Adds some data only with one choice
        form_data = self.get_form_data(unbound_form)
        form_data.update({
            'question_set-0-text': 'text test1',
            'question_set-0-type': 'MultiChoiceWithAnswer',
            'question_set-0-choice_set-0-text': 'choice test 0',
            })
        form_question = QuestionFormSet(instance=self.questionnaire,
                                        data=form_data)
        # Verify if the form is not valid
        self.assertFalse(form_question.is_valid())
        # Add a new choice
        form_data.update({
            'question_set-0-choice_set-1-text': 'choice test 1',
            })
        form_question = QuestionFormSet(instance=self.questionnaire,
                                        data=form_data)
        self.assertTrue(form_question.is_valid())
        form_question.save()
        # verify the data storage (choices)
        question = Question.objects.get(questionnaire=self.questionnaire.id)
        self.assertEqual(
            Choice.objects.filter(question=question.id).count(), 2)

    def test_delete_choice(self):
        # Get the question of type 'multichoices'
        self.test_add_question_type_multichoices()
        form_question = QuestionFormSet(instance=self.questionnaire)

        form_data = self.get_form_data(form_question)
        # Delete a choice
        form_data.update({
            'question_set-0-choice_set-0-DELETE': True,
            'question_set-0-choice_set-2-text': 'choice test 2',
            })
        form_question = QuestionFormSet(instance=self.questionnaire,
                                        data=form_data)
        form_question.save()
        self.assertTrue(form_question.is_valid())
        form_question.save()
        question = Question.objects.get(questionnaire=self.questionnaire.id)
        # verify dat storage (choices)
        self.assertEqual(
            Choice.objects.filter(question=question.id).count(), 2)

    def test_delete_question(self):
        # Add a new question of type `YesNoQuestion`
        unbound_form = QuestionFormSet(instance=self.questionnaire)
        form_data = self.get_form_data(unbound_form)
        form_data.update({
            'question_set-0-text': 'text test1',
            })
        form_question = QuestionFormSet(instance=self.questionnaire,
                                        data=form_data)
        self.assertTrue(form_question.is_valid())
        form_question.save()
        # Delete Question
        form_question = QuestionFormSet(instance=self.questionnaire)
        form_data = self.get_form_data(form_question)

        form_data.update({
            'question_set-0-DELETE': True,
            })
        form_question = QuestionFormSet(instance=self.questionnaire,
                                        data=form_data)
        # Verify if the form is not valid
        self.assertFalse(form_question.is_valid())

    def test_take_questionnaire_by_participant(self):
        # Take questionnaire
        # add a new question `YesNoQuestion`
        self.test_add_question_type_yes_no()
        # Authenticate as user
        login = self.client.login(username=self.user.username, password='test0000')
        self.assertTrue(login)
        data_form = {
            'question_0': "yes",
            'question_1': "yes"
        }
        form = DisplayQuestionsForm(
            questionnaire_id=self.questionnaire.id,
            data=data_form
        )
        self.assertTrue(form.is_valid())
        # store the data
        form.save(user=self.user)
        # verify the answer of participant
        question = Question.objects.filter(questionnaire=self.questionnaire.id)[0]
        self.assertEqual((Answer.objects.
                          get(question=question.id).answer
                          ).encode('utf-8'),
                         '"yes"')
