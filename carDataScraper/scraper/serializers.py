from rest_framework import serializers
from .models import CraigslistCity, VehicleListing, VehiclePhoto

class VehiclePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehiclePhoto
        fields = ['id', 'url']

class VehicleListingSerializer(serializers.ModelSerializer):
    photos = VehiclePhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = VehicleListing
        fields = [
            'id', 'listing_id', 'title', 'price', 'location', 'url', 'image_url', 
            'posted_date', 'state', 'city_name', 'description', 'phone_number', 'photos'
        ]

class CraigslistCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CraigslistCity
        fields = ['id', 'name', 'domain']
