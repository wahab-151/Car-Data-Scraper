from django.urls import path
from .views import ScrapeAllCitiesView, CraigslistCityListView, VehicleListingView
from .views_api import ScrapeFormattedDataView

urlpatterns = [
    path('cars/', ScrapeAllCitiesView.as_view(), name='cars'),
    path('cities/', CraigslistCityListView.as_view(), name='city-list'),
    path('vehicles/', VehicleListingView.as_view(), name='vehicle-list'),
    path('scrape-formatted-data/', ScrapeFormattedDataView.as_view(), name='scrape-formatted-data'),
]
