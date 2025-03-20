from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from datetime import datetime
import logging

from .models import CraigslistCity, VehicleListing, VehiclePhoto
from .serializers import CraigslistCitySerializer, VehicleListingSerializer
from .utils import CraigslistScraper, CRAIGSLIST_CITIES

logger = logging.getLogger(__name__)

class CraigslistCityListView(generics.ListAPIView):
    queryset = CraigslistCity.objects.all()
    serializer_class = CraigslistCitySerializer

class VehicleListingView(generics.ListAPIView):
    serializer_class = VehicleListingSerializer
    
    def get_queryset(self):
        queryset = VehicleListing.objects.all().order_by('-posted_date')
        
        # Filter by city if provided
        city_domain = self.request.query_params.get('city')
        if city_domain:
            queryset = queryset.filter(city__domain=city_domain)
            
        # Filter by search term if provided
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset

class ScrapeAllCitiesView(APIView):
    def get(self, request, format=None):
        """
        Scrape vehicle listings from all Craigslist cities and return the results.
        Results are organized by city name.
        """
        try:
            scraper = CraigslistScraper()
            results = scraper.scrape_all_cities()
            
            # Initialize the database with cities if needed
            self._initialize_cities()
            
            # Save results to database if requested
            save_to_db = request.query_params.get('save', '').lower() == 'true'
            if save_to_db:
                self._save_to_database(results)
            
            # Save results to a JSON file
            save_to_file = request.query_params.get('save_to_file', 'true').lower() == 'true'
            output_file = None
            if save_to_file:
                import json
                from datetime import datetime
                
                # Generate output filename
                if request.query_params.get('output_file'):
                    output_file = request.query_params.get('output_file')
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"craigslist_cars_{timestamp}.json"
                
                # Format the results as requested: [{"newyork":[car1, car2, ...]}, {"alabama":[car1, car2, ...]}]
                formatted_results = []
                for city_name, listings in results.items():
                    # Find the domain for this city
                    city_info = next((city for city in CRAIGSLIST_CITIES if city['name'] == city_name), None)
                    if city_info:
                        city_domain = city_info['domain']
                        formatted_results.append({city_domain: listings})
                
                # Save to file
                with open(output_file, 'w') as f:
                    json.dump(formatted_results, f, indent=2)
                
                logger.info(f"Results saved to {output_file}")
                
                # Add output_file to the response
                response_data = {
                    'results': results,
                    'output_file': output_file
                }
                return Response(response_data)
                
            return Response(results)
            
        except Exception as e:
            logger.error(f"Error in scrape all cities view: {str(e)}")
            return Response(
                {"error": f"Failed to scrape Craigslist cities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _initialize_cities(self):
        """Initialize the database with Craigslist cities if not already present"""
        existing_domains = set(CraigslistCity.objects.values_list('domain', flat=True))
        
        cities_to_create = []
        for city in CRAIGSLIST_CITIES:
            if city['domain'] not in existing_domains:
                cities_to_create.append(CraigslistCity(
                    name=city['name'],
                    domain=city['domain']
                ))
                
        if cities_to_create:
            CraigslistCity.objects.bulk_create(cities_to_create)
            logger.info(f"Added {len(cities_to_create)} new Craigslist cities to the database")
    
    @transaction.atomic
    def _save_to_database(self, results):
        """Save the scraped results to the database"""
        count = 0
        photo_count = 0
        
        for city_name, listings in results.items():
            try:
                # Find the city in the database
                city = CraigslistCity.objects.filter(name=city_name).first()
                if not city:
                    logger.warning(f"City {city_name} not found in database, skipping listings")
                    continue
                
                # Process each listing
                for listing_data in listings:
                    # Skip listings without ID
                    if not listing_data.get('listing_id'):
                        continue
                        
                    # Convert posted_date string to datetime if present
                    posted_date = None
                    if listing_data.get('posted_date'):
                        try:
                            if isinstance(listing_data['posted_date'], str):
                                posted_date = datetime.fromisoformat(listing_data['posted_date'].replace('Z', '+00:00'))
                            else:
                                posted_date = listing_data['posted_date']
                        except:
                            posted_date = datetime.now()
                    
                    # Create or update the listing with new fields
                    listing, created = VehicleListing.objects.update_or_create(
                        city=city,
                        listing_id=listing_data['listing_id'],
                        defaults={
                            'title': listing_data.get('title', ''),
                            'price': listing_data.get('price', ''),
                            'location': listing_data.get('location', ''),
                            'url': listing_data.get('url', ''),
                            'image_url': listing_data.get('image_url', ''),
                            'posted_date': posted_date,
                            # New fields
                            'state': listing_data.get('state', ''),
                            'city_name': listing_data.get('city', ''),
                            'description': listing_data.get('description', ''),
                            'phone_number': listing_data.get('phone_number', ''),
                        }
                    )
                    
                    # Save photos
                    if listing_data.get('photo_urls'):
                        # Delete existing photos to avoid duplicates
                        if not created:
                            VehiclePhoto.objects.filter(vehicle=listing).delete()
                        
                        # Create new photo objects
                        photos_to_create = []
                        for photo_url in listing_data['photo_urls']:
                            if photo_url:  # Skip empty URLs
                                photos_to_create.append(VehiclePhoto(
                                    vehicle=listing,
                                    url=photo_url
                                ))
                        
                        if photos_to_create:
                            VehiclePhoto.objects.bulk_create(photos_to_create)
                            photo_count += len(photos_to_create)
                    
                    count += 1
                    
            except Exception as e:
                logger.error(f"Error saving listings for {city_name}: {str(e)}")
        
        logger.info(f"Saved {count} vehicle listings to the database")
