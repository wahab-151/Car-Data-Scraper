from django.db import models

class CraigslistCity(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    class Meta:
        verbose_name_plural = "Craigslist Cities"

class VehicleListing(models.Model):
    city = models.ForeignKey(CraigslistCity, on_delete=models.CASCADE, related_name='listings')
    listing_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    price = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    posted_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields
    state = models.CharField(max_length=100, null=True, blank=True)
    city_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.price}"
    
    class Meta:
        unique_together = ('city', 'listing_id')

class VehiclePhoto(models.Model):
    vehicle = models.ForeignKey(VehicleListing, on_delete=models.CASCADE, related_name='photos')
    url = models.URLField(max_length=500)
    
    def __str__(self):
        return f"Photo for {self.vehicle.title}"
