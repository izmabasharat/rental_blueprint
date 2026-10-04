# Rental Blueprint: marketplace upgrade

**Status: written but NOT run.** The sandbox I worked in had no Django and no internet, so I could only
syntax-check the Python and check the templates for balanced tags. Expect to fix a small typo or two on first run.

**What your zip contained:** only `rentals/{models,forms,views,urls}.py`, `accounts/models.py` and two templates.
It had no `settings.py`, `manage.py`, project `urls.py`, `base.html` or migrations, so I couldn't inspect those.
Everything below is written to slot into a normal project.

## 1. Files changed / added
Changed (your original logic is kept; additions are at the bottom or marked "added"):
- `rentals/models.py`: new fields on `RentalListing` (purpose, property_type, sale_price, city, area, bedrooms, bathrooms, size_sqft, amenities, is_featured); `price_per_day` is now optional (sale listings use `sale_price`). New models: `ListingImage`, `Favorite`, `Inquiry`. `Booking` and `Review` untouched.
- `rentals/forms.py`: `BookingForm` untouched. Added `ListingForm`, `InquiryForm`, `ReviewForm`, `SearchForm`.
- `rentals/views.py`: original views kept (detail view extended, booking POST now refuses sale/inactive listings). Added home, search, favourites, inquiry, review, user dashboard, vendor CRUD, vendor inquiries/requests.
- `rentals/urls.py`: original 4 routes kept, new ones added.
- `templates/rentals/listing_detail.html` (rewritten, your booking card + JS kept) and `vendor_dashboard.html` (restyled, same context).

New:
- `rentals/admin.py`, `rentals/context_processors.py`, `rentals/templatetags/rental_extras.py`
- `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`
- `templates/base.html` (Tailwind CDN, same block names as before: title, extra_head, content, extra_js)
- `templates/rentals/`: home, property_list, favorites, user_dashboard, vendor_properties, listing_form, vendor_inquiries, vendor_requests, property_unavailable, `partials/*`
- `templates/registration/login.html`, `register.html`, `templates/accounts/profile.html`

If you already have a `base.html` or `admin.py`, merge instead of overwriting.

## 2. Settings and URL wiring (your project files)
```python
# settings.py
AUTH_USER_MODEL = "accounts.CustomUser"
INSTALLED_APPS += ["accounts", "rentals"]          # if not already there
TEMPLATES[0]["OPTIONS"]["context_processors"] += ["rentals.context_processors.favorites"]
MEDIA_URL = "/media/"; MEDIA_ROOT = BASE_DIR / "media"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "rentals:after_login"
LOGOUT_REDIRECT_URL = "rentals:home"
CURRENCY_SYMBOL = "$"          # e.g. "Rs " for Pakistan
```
```python
# project urls.py
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),               # must come first (register, profile)
    path("accounts/", include("django.contrib.auth.urls")),    # login, logout ("login"/"logout" names)
    path("", include("rentals.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
Requires Django 5.1+ (your `CheckConstraint(condition=...)` already needs it) and `pip install pillow`.

## 3. Run
```
pip install django pillow
python manage.py makemigrations accounts rentals
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Homepage: **http://127.0.0.1:8000/**. Existing listings get defaults (Rent, House, empty city); edit them to fill in city/area.

## 4. URLs
`/` home · `/properties/` search · `/listings/<id>/` details (your original route) · `/accounts/login/` · `/accounts/register/` ·
`/account/` user dashboard · `/favorites/` · `/dashboard/` vendor dashboard (your original route) ·
`/dashboard/properties/` · `/dashboard/properties/add/` · `/dashboard/inquiries/` · `/dashboard/requests/`

## 5. Interview demo script
1. Register as **Vendor** (register page, second option) → lands on vendor dashboard → *Add property* (upload cover + gallery, choose Rent) → Publish. Add one more as **Buy**.
2. Log out. Register as a **Customer**.
3. Homepage → type the city → Search → use filters/sort on the results page (count reads "N Properties Found in <city>").
4. Open a property → gallery, amenities, agent, similar properties → tap the heart (Saved) → *Contact agent* form → success message.
5. On a rent listing pick dates → live price/availability → *Request to book*.
6. `/account/`: saved properties (remove), inquiries with status, booking requests (cancel pending).
7. Log in as the vendor: inquiries page (mark replied), approve the booking, deactivate/edit a property.
8. Reviews: appear after a confirmed booking whose check-out date has passed (existing rule, kept). Fastest demo: approve a booking, then in admin change its dates to the past.

## 6. Not implemented / limits
- **Prices are per day.** Your booking engine is nightly; I did not convert to monthly rent.
- **Buying has no offer/purchase flow**, only inquiry (there was no backend for it).
- Price filter on a mixed Buy+Rent search compares daily rent with sale prices; pick Buy or Rent to filter meaningfully.
- No phone number on the user profile (needs a `CustomUser` field). The phone is captured per inquiry instead.
- Inquiries require login. No email notification is sent to the vendor (needs email settings).
- Listings with booking history can't be deleted (`Booking.listing` is PROTECT); deactivate instead.
- Cover image is required; changing it replaces it, and extra photos are added/removed separately.
- "Featured" = `is_featured` flag set in admin (falls back to top-rated).
- Tailwind is loaded from the CDN (fine for demos; use the Tailwind CLI for production).

## 7. Round 2 (UI upgrade)
- Tailwind (chosen over Bootstrap), FontAwesome and Google Font Inter now load in `base.html`; the navbar moved to `partials/_navbar.html` (logged out / buyer / vendor states + profile dropdown).
- `property_list.html`: left filter sidebar (collapses behind a Filters button on mobile).
- `listing_detail.html`: photo slider (arrows, thumbnails, keyboard, swipe).
- `vendor_dashboard.html`: metrics (views, leads) and a listings table with Edit/Delete. New field `RentalListing.view_count`, counted on each visit by non-owners (run `makemigrations` again if you already migrated).
- `user_dashboard.html`: "Recent searches" (stored in the session, last 5, no database).
- `listing_form.html`: drag-and-drop upload zones with thumbnails.
- Login/register: split layout with Log in / Register tabs, red error styling, buyer/vendor picker, live password-match check.
