# algotrade-simulator

this is a django web application based intended to run a simulator resmbling to tel-aviv 35/50/125 charts

## installation
The following installation instructions are for linux terminal.
for windows you can simply download python and pip official installation and use the same pip commands on cmd application.

###First install python and pip:
sudo apt-get install python2.7
sudo apt-get install python-pip

###Then install the project's dependencies:
pip install Django==1.10.4
pip install django-appconf==1.0.2
pip install django-bootstrap-form==3.2.1
pip install django-configurations==2.0
pip install django-cors-headers==1.3.1
pip install numpy==1.12.1
pip install pandas==0.20.1
pip install plotly==2.0.10

there is nothing special with the specified versions of the packges.
those are simply the versions that we used and want to make sure there wont be any compatibility issues with newer versions.

###Run the server

simply use the following command from the root directory of the project:
python src/manage.py runserver <port>

for example:
python src/manage.py runserver 8888

this will start the local server and the application will be available in localhost:<port> or 127.0.0.1:<port> (127.0.0.1:8888 from the example).

this project can run and debugged from pycharm - jetbrains IDE for python.
to configure pycharm to run the application set the script to be src/manage.py and script parameters to be: runserver <port>