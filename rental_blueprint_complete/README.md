# Rental Blueprint – Property Marketplace

A modern Django-based property marketplace where users can buy/rent properties and vendors can list, manage and receive inquiries.

## Quick Start

### 1. Clone and setup
```bash
git clone <your-repo>
cd rental_blueprint_complete
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the database and admin user
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 3. Run the server
```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Project Structure
```
rental_blueprint_complete/
├── manage.py                           # Django CLI
├── db.sqlite3                          # Database (created on first migrate)
├── media/                              # User uploads (property photos)
├── requirements.txt                    # Python dependencies
├── rental_blueprint_project/           # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── __init__.py
├── accounts/                           # User authentication app
│   ├── models.py                       # CustomUser model
│   ├── forms.py                        # Registration & profile forms
│   ├── views.py                        # Register, profile, login
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── __init__.py
├── rentals/                            # Marketplace app
│   ├── models.py                       # RentalListing, Booking, Review, Favorite, Inquiry, etc.
│   ├── forms.py                        # Search, listing, inquiry, review forms
│   ├── views.py                        # Homepage, search, detail, vendor dashboard, etc.
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py           # Favorites in every template
│   ├── templatetags/rental_extras.py   # Money filter, stars filter
│   └── __init__.py
└── templates/
    ├── base.html                       # Master layout
    ├── registration/
    │   ├── login.html
    │   └── register.html
    ├── accounts/
    │   └── profile.html
    └── rentals/
        ├── home.html
        ├── property_list.html
        ├── listing_detail.html
        ├── favorites.html
        ├── user_dashboard.html
        ├── vendor_dashboard.html
        ├── vendor_properties.html
        ├── vendor_inquiries.html
        ├── vendor_requests.html
        ├── listing_form.html
        ├── property_unavailable.html
        └── partials/
            ├── _navbar.html
            ├── _card.html
            ├── _field.html
            ├── _stars.html
            ├── _status.html
            ├── _vendor_nav.html
            ├── _auth_shell.html
            └── _messages.html
```

## Default URLs

| Route | Purpose |
|-------|---------|
| `/` | Homepage |
| `/properties/` | Search & filter |
| `/listings/<id>/` | Property details |
| `/login/` | Login |
| `/accounts/register/` | Register (buyer or vendor) |
| `/account/` | User dashboard (saved, inquiries, bookings) |
| `/favorites/` | Saved properties |
| `/dashboard/` | Vendor dashboard (overview, metrics) |
| `/dashboard/properties/` | Vendor's listings |
| `/dashboard/properties/add/` | Add new listing |
| `/dashboard/properties/<id>/edit/` | Edit listing |
| `/dashboard/inquiries/` | Inquiries inbox |
| `/dashboard/requests/` | Booking requests |
| `/admin/` | Django admin |

## Key Features

✅ **For Buyers/Renters:**
- Search properties by location, type, price, beds, baths
- Photo gallery with slider (arrows, thumbnails, swipe, keyboard)
- Save favorite properties
- Send inquiries to agents
- Track booking requests

✅ **For Vendors/Agents:**
- List properties with drag-and-drop photo upload (cover + gallery)
- View performance metrics (property views, total leads)
- Manage active/inactive listings
- Inbox for inquiries (mark replied)
- Approve/reject booking requests

✅ **General:**
- Responsive design (mobile, tablet, desktop)
- Clean, modern UI with Tailwind CSS & FontAwesome
- Reviews & ratings (after confirmed stays)
- Session-based recent searches
- User profiles & role-based dashboards

## First Run Demo

1. **Register as a Vendor**: `/accounts/register/` → select "Agent/Owner"
2. **Add a property**: Vendor dashboard → Add property
3. **Logout** and **register as a Buyer**: `/accounts/register/` → select "Buyer/Renter"
4. **Search**: homepage → type city → search
5. **Save & contact**: click heart icon to save, send inquiry
6. **Dashboard**: see saved properties, inquiries, booking requests

## Customization

### Change currency symbol
Edit `CURRENCY_SYMBOL` in `rental_blueprint_project/settings.py`:
```python
CURRENCY_SYMBOL = "Rs "  # For Pakistan
```

### Add new fields to listings
1. Edit `RentalListing` in `rentals/models.py`
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`
4. Update the form in `rentals/forms.py`
5. Update templates as needed

### Deployment (production)
1. Set `DEBUG = False` in settings.py
2. Generate a new `SECRET_KEY` (use a proper generator)
3. Update `ALLOWED_HOSTS`
4. Use a production database (PostgreSQL recommended)
5. Collect static files: `python manage.py collectstatic`
6. Use a production WSGI server (gunicorn, uWSGI)

## Troubleshooting

**"ModuleNotFoundError: No module named 'django'"**
→ Run `pip install -r requirements.txt`

**"OperationalError: no such table"**
→ Run `python manage.py migrate`

**"ImportError: No module named 'accounts.apps'"**
→ Make sure `accounts/apps.py` exists (it's in this repo)

**Photos not showing**
→ Check `MEDIA_URL` and `MEDIA_ROOT` in settings, ensure `/media/` folder exists

## License
This project is free to use and modify for educational purposes.

---
**Built with ❤️ using Django, Tailwind CSS, and FontAwesome**
