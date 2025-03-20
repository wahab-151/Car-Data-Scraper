from django.contrib import admin
from .models import CraigslistCity, VehicleListing

@admin.register(CraigslistCity)
class CraigslistCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain')
    search_fields = ('name', 'domain')

@admin.register(VehicleListing)
class VehicleListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'city', 'location', 'posted_date')
    list_filter = ('city', 'posted_date')
    search_fields = ('title', 'location', 'price')