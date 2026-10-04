from django.contrib import admin
from .models import Booking, Favorite, Inquiry, ListingImage, RentalListing, Review


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(RentalListing)
class RentalListingAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "purpose", "property_type", "city", "is_active", "is_featured")
    list_filter = ("purpose", "property_type", "is_active", "is_featured", "city")
    search_fields = ("title", "city", "area", "location")
    inlines = [ListingImageInline]


admin.site.register([Booking, Review, Favorite, Inquiry])
