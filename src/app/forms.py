from django import forms


class SimulatorForm(forms.Form):
    num_stocks = forms.DecimalField(min_value=1, label='Number of stocks',
                                    required=True, initial=25)
    max_weight = forms.DecimalField(min_value=1, max_value=100, label='Maximum stock weight (%)',
                                    required=True, initial=7)
    update_freq = forms.DecimalField(min_value=1, max_value=300, label='Update frequency (days)',
                                     required=True, initial=100)

    class Meta:
        ordering = ('num_stocks', 'max_weight', 'update_freq')
