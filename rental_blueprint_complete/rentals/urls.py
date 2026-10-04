# rentals/urls.py   (project urls.py: path("", include("rentals.urls")))
from django.urls import path
from . import views

app_name = "rentals"
urlpatterns = [
    # ---- original routes (unchanged) ----
    path("listings/<int:pk>/", views.RentalListingDetailView.as_view(), name="detail"),
    path("listings/<int:pk>/quote/", views.price_quote, name="quote"),
    path("dashboard/", views.VendorDashboardView.as_view(), name="dashboard"),
    path("dashboard/bookings/<int:pk>/<str:action>/", views.BookingDecisionView.as_view(), name="booking_decision"),

    # ---- public marketplace ----
    path("", views.HomeView.as_view(), name="home"),
    path("properties/", views.PropertyListView.as_view(), name="list"),
    path("listings/<int:pk>/inquiry/", views.send_inquiry, name="send_inquiry"),
    path("listings/<int:pk>/review/", views.submit_review, name="submit_review"),

    # ---- signed-in users ----
    path("go/", views.after_login, name="after_login"),
    path("account/", views.UserDashboardView.as_view(), name="account"),
    path("account/bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("favorites/", views.FavoritesView.as_view(), name="favorites"),
    path("favorites/toggle/<int:pk>/", views.toggle_favorite, name="toggle_favorite"),

    # ---- vendor area ----
    path("dashboard/properties/", views.VendorPropertiesView.as_view(), name="vendor_properties"),
    path("dashboard/properties/add/", views.ListingCreateView.as_view(), name="add_property"),
    path("dashboard/properties/<int:pk>/edit/", views.ListingUpdateView.as_view(), name="edit_property"),
    path("dashboard/properties/<int:pk>/toggle/", views.listing_toggle_active, name="toggle_property"),
    path("dashboard/properties/<int:pk>/delete/", views.listing_delete, name="delete_property"),
    path("dashboard/inquiries/", views.VendorInquiriesView.as_view(), name="vendor_inquiries"),
    path("dashboard/inquiries/<int:pk>/replied/", views.inquiry_mark_replied, name="inquiry_replied"),
    path("dashboard/requests/", views.VendorRequestsView.as_view(), name="vendor_requests"),
]
