from django import forms
import os


def get_indices():
    indices_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stockIdx')
    indices = os.listdir(indices_dir)
    indices = [(x[:-4], x[:-4]) for x in indices]
    indices = sorted(indices, key=lambda a: a[0])
    return indices


class SimulatorForm(forms.Form):
    num_stocks = forms.DecimalField(min_value=1, label='Number of stocks',
                                    required=True, initial=40)
    max_weight = forms.DecimalField(min_value=1, max_value=100, label='Maximum stock weight (%)',
                                    required=True, initial=7)
    compare_to_index = forms.ChoiceField(choices=get_indices(), required=True)
    with_us_stocks = forms.TypedChoiceField(widget=forms.RadioSelect, choices=((False, 'No'), (True, 'Yes')),
                                            coerce=lambda x: x == 'True', initial=False, required=True,
                                            label='With US stocks?')

    class Meta:
        ordering = ('num_stocks', 'max_weight', 'compared_index', 'with_us_stocks')
