from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
import json
import os
from datetime import datetime

from .utils.scrape_and_format import scrape_and_format_data
from .views import ScrapeAllCitiesView

logger = logging.getLogger(__name__)

class ScrapeFormattedDataView(APIView):
    def get(self, request, format=None):
        """
        Scrape car data from Craigslist for all USA cities and return the results
        in the requested format: [{"newyork":[car1, car2, ...]}, {"alabama":[car1, car2, ...]}]
        """
        try:
            # Get query parameters
            max_workers = int(request.query_params.get('max_workers', 10))
            save_to_db = request.query_params.get('save_to_db', '').lower() == 'true'
            save_to_file = request.query_params.get('save_to_file', 'true').lower() == 'true'
            
            # Generate output filename if saving to file is requested
            output_file = None
            if save_to_file and request.query_params.get('output_file'):
                output_file = request.query_params.get('output_file')
            
            # Call the scrape_and_format_data function
            results, output_file_path = scrape_and_format_data(
                max_workers=max_workers,
                output_file=output_file,
                save_to_db=save_to_db,
                save_to_file=save_to_file
            )
            
            # Prepare response
            response_data = {
                'success': True,
                'message': f'Successfully scraped data from {len(results)} cities',
                'cities_count': len(results),
                'results': results
            }
            
            if save_to_file:
                response_data['output_file'] = output_file_path
                
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in scrape formatted data view: {str(e)}")
            return Response(
                {"error": f"Failed to scrape Craigslist cities: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
