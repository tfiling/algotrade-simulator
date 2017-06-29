from django.contrib import messages
from django.shortcuts import render
from django.template.defaultfilters import mark_safe
from forms import SimulatorForm
from graph_creator import create_graph
import stocks_data


def home(request):
    form = SimulatorForm()
    if request.method == 'POST':
        form = SimulatorForm(request.POST)
        if form.is_valid():
            index_name = form.cleaned_data['compare_to_index']
            real_data = stocks_data.getStockIndex(index_name)
            simulated_data, sharpe, std, avg_profit = stocks_data.computeNewIndex(
                numOfStocks=form.cleaned_data['num_stocks'],
                weightLimit=float(form.cleaned_data['max_weight'])/100.0,
                withUS=form.cleaned_data['with_us_stocks'],
                indexName=index_name)

            graph = mark_safe(create_graph(simulated_data, real_data))
            return render(request, 'index.html', {'upload': False, 'graph': graph, 'sharpe':sharpe,
                                                  'std': std, 'avg_profit': avg_profit})
            # messages.warning(request, 'Input file should be a CSV file only.')
    return render(request, 'index.html', {'upload': True, 'form': form})
