from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
import plotly.plotly as plotly
import plotly.graph_objs as go
import plotly.offline
import pandas as pd
import views


# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^$', views.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
