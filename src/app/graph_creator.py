import plotly.graph_objs as go
import plotly.offline


def create_graph(simulated_index, real_index=None, sharpeRatio = None, standardDeviation=None, averageReturn=None):
    """
    :param simulated_index: dataframe with simulated index data
    :param real_index: dataframe with real index data
    :return: html div of the graph
    """
    simulated = go.Scatter(x=simulated_index.date, y=simulated_index.value,
                           name='Simulated index', line=dict(color='#17BECF'), opacity=0.8)
    data = [simulated]

    if real_index is not None:
        real = go.Scatter(x=real_index.date, y=real_index.value,
                          name='Real index', line=dict(color='#7F7F7F'), opacity=0.8)
        data.append(real)

    layout = dict(
        title='Simulated index VS. Real index',
        autosize=True,
        paper_bgcolor='transparent',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label='1w', step='day'),
                    dict(count=1, label='1m', step='month'),
                    dict(count=6, label='6m', step='month'),
                    dict(count=1, label='1y', step='year'),
                    dict(count=3, label='3y', step='year'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(),
            type='date'
        )
    )
    fig = dict(data=data, layout=layout)
    div = '<div style="height: 95vh;background: rgba(255, 255, 255, 0.8);">'
    return plotly.offline.plot(fig, output_type='div').replace('<div>', div, 1)
