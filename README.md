# algotrade-simulator

this is a django web application based intended to run a simulator resmbling to tel-aviv 35/50/125 charts.
the simulator is based on data between the dates 31/5/2012-29/5/2017 and will calculate the chart for those dates. 
the data is static within the project and located in:
- /IL_stocks - the israeli stocks
- /US_stocks - the american stocks specified by ofer zevin
- /stockIdx - tel-aviv 35/50/125 charts

the HTML, js and CSS assets ar located in the /static folder.
the python code that handles the HTTP requests is located in /src/app/views.py
the server handles HTTP post requests containing the form filled by the user with the required parameters: 
- how many stocks should be included in the simulated charts
- the maximum weight for a stock in the chart
- which real chart the sumulated chart should be compared to (tel-aviv 35/50/125)
- a flag indicating if american stocks(specified by ofer zevin) to be integrated into the real chart campared with the simulated chart

the core of the simulator is implemented in /src/app/stocks_data.py
the arguments of the request are extracted and sent as arguments to the following functions in that script:
- getStockIndex - reads and returns the real chart's data that will be compared with the simulated one
- computeNewIndex - the main function of the simulator that runs the simulator

##### important!
once the form of the web application is submitted the simulator starts. 
the calculation takes 15-20 minutes, a feedback is shown in the local server's output. each day in the chart that was calculated is printed with it's chart value.
when the simulator runs there is no loading indication except the web browser's page loading indication.

when the simulator finished its calculation an interactive praph with both simulated and real charts will be displayed.

the results of every succesful run of the simulator is saved to a csv and pkl files in /newIndices
if the user configures the simulator to run with the same arguments as a previous run the results will instantly load and shown.

the server also prints a log file for every run into /log folder. it includes the weight and value of every stock in the chart for ever simulated date.


## installation
The following installation instructions are for linux terminal.
for windows you can simply download python and pip official installation and use the same pip commands on cmd application.

### First install python and pip:
- sudo apt-get install python2.7
- sudo apt-get install python-pip

### Then install the project's dependencies:
- pip install Django==1.10.4
- pip install django-appconf==1.0.2
- pip install django-bootstrap-form==3.2.1
- pip install django-configurations==2.0
- pip install django-cors-headers==1.3.1
- pip install numpy==1.12.1
- pip install pandas==0.20.1
- pip install plotly==2.0.10

there is nothing special with the specified versions of the packges.
those are simply the versions that we used and want to make sure there wont be any compatibility issues with newer versions.

### Run the server

simply use the following command from the root directory of the project:
python src/manage.py runserver <port>

for example:
python src/manage.py runserver 8888

this will start the local server and the application will be available in localhost:<port> or 127.0.0.1:<port> (127.0.0.1:8888 from the example).

this project can run and debugged from pycharm - jetbrains IDE for python.
to configure pycharm to run the application set the script to be src/manage.py and script parameters to be: runserver <port>