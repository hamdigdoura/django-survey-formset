(function () {
    'use strict';

    var addChoice;
    var _Y_ = window;

    function updateElementIndex(el, prefix, ndx, clsChoiceQst) {
        /**
         * Update or change the prefix of Formset with an index
         * @el: element of formset
         * @prefix: prefix like `question_set_0_choice-set`
         * @ndx: the new index of formset
         */
        var replacement;
        if (clsChoiceQst.indexOf('choice') === -1) {
            // Question-Set
            el.id = el.id.replace(/__prefix__/g, ndx);
            replacement = $(el).html().replace(/question_set-__prefix__/g, 'question_set-' + ndx);
            $(el).html(replacement);
        }
        else {
            /*** ChoiceSet ***/
            el.id = prefix+'-'+(ndx)+'-order';

            /*** Change index in Adding choice-set ***/
            replacement = $(el).html().replace(/question_set-__prefix__/g, prefix.split('-choice_set')[0]);
            replacement = replacement.replace(/choice_set-__prefix__/g, 'choice_set-'+(ndx));

            /*** Change index in Deleting choice-set ***/

            var $fieldChoice = $('#id_'+prefix+'-'+(ndx+1)+'-text');

            // Get the value from next Field and put it in the current field (to delete)
            var valueOldChoice = $fieldChoice.val();

            // change the index of form with a new one
            replacement = replacement.replace(/choice_set-[^d]/g, 'choice_set-'+ndx);
            $(el).html(replacement);

            if(typeof valueOldChoice !== 'undefined' && valueOldChoice !== '') {
                $('#id_'+prefix+'-'+ndx+'-text').val(valueOldChoice);
            }

        }
    }


    _Y_.addFormSet = function(btn, prefixFormset, listClassFormSets, emptyFormset) {
        /***
         * Add a new formset (ChoiceSet or QuestionSet)
         * @prefixFormset: prefix
         * @listClassFormsets: List of formset
         * @emptyFormset: Empty form will be cloned
         * @type {*|jQuery|HTMLElement}
         */

        var $totalForms = $('#id_' + prefixFormset + '-TOTAL_FORMS')
            , $maxNumForms = $("#id_" + prefixFormset + "-MAX_NUM_FORMS");

        // @valMaxNumForms: Max Number of Formsets (choice-set or question-set)
        // for example for choice-set. We have the possiblity for only 8 Choices
        // @valTotalForms: Total of Formset(Choice-set or Question-set )
        var valMaxNumForms = parseInt($maxNumForms.val())
            , valTotalForms = parseInt($totalForms.val());

        //We use to compare only for Choice-set. For Question-Formset,  we have
        // the possiblity to add until 100 questions
        if ((valTotalForms < valMaxNumForms) || (emptyFormset === 'empty-question')) {

            // Gets the empty Formset and clones it
            var row = $('.' + emptyFormset).children().clone(true).get(0);
            // insert the clone of empty Formset in the last item of {{listClassFormSets}} and show it
            $(row).insertAfter($('.' + listClassFormSets + ':last')).removeClass('hide').addClass(listClassFormSets);
            // Here, we have to change the id and the name of field that we are adding
            // initially id and name are: `id_question_set-__prefix__-choice_set-__prefix__-text`
            // finally, the result will be like: `id_question_set-{{id}}-choice_set-{{id}}-text`
            $(row).each(function () {
                updateElementIndex(this, prefixFormset, valTotalForms, emptyFormset);
            });
            /* Update the total of (question form or choice form)*/
            $totalForms.val(valTotalForms + 1);
            if(emptyFormset === 'empty-question') {
                $('.'+prefixFormset+'-add').detach();
            }
        }
        else {
            addChoice = $('.'+prefixFormset+'-add').detach();
        }
    };

    _Y_.orderingListForm = function() {
        /***
         * Update the order of list's formset
         * @type {number}
         */
        var i = 0;
        $('.itemTodrag').not(':hidden').each(function(){
            var questionPrefix = (this.id).replace('-list', '');
            $('#id_'+questionPrefix+'-ORDER').val(i+1);
            $('#'+questionPrefix+'-counter').text(i+1);
            i++;
        });


    }

    _Y_.deleteFormSet = function (btn, prefix, idClass, clsChoiceQst) {
        /**
         * Delete a Formset (QuestionSet or ChoiceSet)
         * @prefix question_set-0-choice_set
         * @idClass dynamic-form-choice-question_set-0
         * @clsChoiceQst question_set-0-choice_set-4
         * @type {*|jQuery|HTMLElement}
         */

        var $totalForms = $('#id_' + prefix + '-TOTAL_FORMS')
            , $deleteForm = $("#id_" + clsChoiceQst + "-DELETE")
            , $maxNumForms = $("#id_" + prefix + "-MAX_NUM_FORMS")
            , $deleteNumForms = $("#id_"+prefix+"-DEL_NUM_FORMS")
            , $initialNumForms = $("#id_"+prefix+"-INITIAL_FORMS");

        var valMaxNumForms = parseInt($maxNumForms.val())
            , valTotalForms = parseInt($totalForms.val())
            , valDelNumForms = parseInt($deleteNumForms.val())
            , valInitNumForms = parseInt($initialNumForms.val());
        var ndx = parseInt(clsChoiceQst.match(/\d+$/));
        var verifForm = false;

        if (idClass === '') {
            // Min Form Question (Min 1)
            verifForm = ((valInitNumForms - valDelNumForms) > 1);
        }
        else {
            // Max of number Forms choice to delete (8 max, 2 min)
            var nbrOfFormToDelete = 6;
            verifForm = !((valMaxNumForms - valTotalForms) >= nbrOfFormToDelete);
        }

        if (verifForm) {
            // Delete Form was existed

            if (typeof ($deleteForm.val()) !== 'undefined') {
                // Check the check box of form
                $deleteForm.prop('checked', true);

                if (idClass === '') {
                    var $itmQuestionlst = $('#'+clsChoiceQst+'-list');
                    var toChgIndx = parseInt($('#'+clsChoiceQst + '-counter').text());
                    $deleteNumForms.val(valDelNumForms + 1);
                    $itmQuestionlst.hide();
                    orderingListForm();
                }
                else {
                    // Hide the Form
                    $('#'+clsChoiceQst + '-order').hide();
                    // update the max form choice
                    $maxNumForms.val(valMaxNumForms + 1);
                }
            } else
            {
                // Delete Form Choice
                var choiceForms = $('.'+idClass);
                $('#'+clsChoiceQst+'-order').remove();
                for (var i = (ndx+1), formCount=choiceForms.length; i<formCount; i++) {
                    $(choiceForms.get(i)).each(function(){
                        updateElementIndex(this, prefix, (i-1), clsChoiceQst);
                    });

                }
                $totalForms.val(valTotalForms - 1);
            }
        }
    };

    _Y_.collapseChoice = function (prefix) {
        /***
         * Collapsing the Formset when the type of question is Multi-choices
         */
        $("input[name$=" + prefix + "-type]").change(function () {
            var valChoice = $(this).val();
            var $dsplyRadioEl = $("#" + prefix + "-display")
                , $hidRadioEl = $(".display-none-" + prefix);

            if (valChoice === 'MultiChoices' || valChoice === 'MultiChoiceWithAnswer') {
                // collapsing
                $hidRadioEl.hide();
                $dsplyRadioEl.show();
            } else {
                $hidRadioEl.show();
                $dsplyRadioEl.hide();
            }
        });
        $("input[name$=" + prefix + "-type]:checked").change();
    };

    _Y_.formError = function(prefix) {
        /***
         * Collapsing the QUestionSet when an error was detected
         */
       $('#'+prefix+'-list').children(':first').addClass('active');
        window.location.hash = prefix+'-list';
    };
})();