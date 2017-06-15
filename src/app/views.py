from django.contrib import messages
from django.shortcuts import render
from django.template.defaultfilters import mark_safe
from forms import SimulatorForm
from graph_creator import create_graph
import stocks_data
import os
import pandas as pd


def home(request):
    form = SimulatorForm()
    if request.method == 'POST':
        form = SimulatorForm(request.POST)
        if form.is_valid():
            simulated_data = stocks_data.computeNewIndex(numOfStocks=form.cleaned_data['num_stocks'],
                                                         weightLimit=float(form.cleaned_data['max_weight'])/100.0,
                                                         withUS=form.cleaned_data['with_us_stocks'])

            # simulated_data = pd.read_csv(os.path.dirname(os.path.dirname(__file__)) + '/newindex_15_1.csv')
            real_data = stocks_data.getStockIndex(form.cleaned_data['compare_to_index'])
            graph = mark_safe(create_graph(simulated_data, real_data))
            return render(request, 'index.html', {'upload': False, 'graph': graph})
        # messages.warning(request, 'Input file should be a CSV file only.')
    return render(request, 'index.html', {'upload': True, 'form': form})
