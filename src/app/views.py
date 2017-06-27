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

# <<<<<<< HEAD
#             (simulated_data, sharpeRatio, standardDeviation, averageReturn) = stocks_data.computeNewIndex(numOfStocks=form.cleaned_data['num_stocks'],
#                                                          weightLimit=float(form.cleaned_data['max_weight'])/100.0,
#                                                          withUS=form.cleaned_data['with_us_stocks'],
#                                                          real_index = real_data)
#
#             # simulated_data = pd.read_csv(os.path.dirname(os.path.dirname(__file__)) + '/newindex_15_1.csv')
#             graph = mark_safe(create_graph(simulated_data, real_data, sharpeRatio, standardDeviation, averageReturn))
#             return render(request, 'index.html', {'upload': False, 'graph': graph})
# =======
            graph = mark_safe(create_graph(simulated_data, real_data))
            return render(request, 'index.html', {'upload': False, 'graph': graph, 'sharpe':sharpe,
                                                  'std': std, 'avg_profit': avg_profit})
# >>>>>>> e6c0fc8476e75a567965971293f1ae91cd424be3
            # messages.warning(request, 'Input file should be a CSV file only.')
    return render(request, 'index.html', {'upload': True, 'form': form})
