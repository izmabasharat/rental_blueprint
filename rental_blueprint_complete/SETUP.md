# 🏠 Rental Blueprint – Setup Guide

Everything is included. No files to hunt for.

## ⚡ 3-Minute Start

### 1️⃣ Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Create the database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3️⃣ Create an admin user
```bash
python manage.py createsuperuser
```
Follow the prompts. You can use:
- **Username:** `admin`
- **Email:** `admin@example.com`
- **Password:** something memorable for testing

### 4️⃣ Run the server
```bash
python manage.py runserver
```

### 5️⃣ Open in your browser
Go to **http://127.0.0.1:8000/**

---

## 📋 What You Just Got

✅ **Complete Django project** – all config, settings, database ready  
✅ **User authentication** – login, register, profiles  
✅ **Property marketplace** – search, filter, details, gallery slider  
✅ **Vendor tools** – add listings, manage properties, view inquiries  
✅ **Buyer tools** – save favorites, send inquiries, track bookings  
✅ **Modern UI** – responsive design, Tailwind CSS, FontAwesome icons  
✅ **Database models** – users, listings, photos, reviews, inquiries, bookings  
✅ **Admin panel** – manage everything at `/admin/`  

---

## 🚀 Demo Flow (5 minutes)

### Step 1: Create a vendor account
1. Go to http://127.0.0.1:8000/accounts/register/
2. Choose **"I'm an agent / owner"**
3. Fill in name, email, password
4. **Register**

### Step 2: Add a property
1. Click **"Vendor dashboard"** in the top menu
2. Click **"+ Add New Listing"**
3. Fill in:
   - **Title:** "Cozy 2BR apartment in Lahore"
   - **Description:** "Beautiful, newly renovated apartment near the mall"
   - **Buy or Rent:** Choose **"Rent"**
   - **Price per day:** `1500`
   - **City:** `Lahore`
   - **Area:** `DHA Phase 5`
   - **Bedrooms:** `2`
   - **Bathrooms:** `1`
   - **Size (sq ft):** `1200`
   - **Cover image:** Upload any image (it will be resized)
4. Click **"Publish property"**
5. Add 1-2 more properties (vary the location/price)

### Step 3: View as a buyer
1. **Log out** (top menu → Log out)
2. Go to http://127.0.0.1:8000/accounts/register/
3. Choose **"I want to buy/rent a property"**
4. **Register** as a buyer

### Step 4: Search properties
1. Go to the **homepage** (click logo)
2. Type `Lahore` in the search box
3. Click **"Search properties"**
4. Use filters on the left (price, bedrooms, etc.)
5. Click **"View details"** on a property

### Step 5: Interact with a property
On the property detail page:
- **Click the heart** to save it (top right)
- **Scroll down** to see full description, amenities, agent info
- **View the photo gallery** (arrows, thumbnails, swipe on mobile)
- **Send an inquiry** – fill in your name, email, phone, message

### Step 6: Check your account
1. Click **"My account"** (top menu)
2. See:
   - Saved properties (with remove buttons)
   - Inquiries you've sent (with status)
   - Booking requests (if you booked a rental)
   - Recent searches

### Step 7: Vendor – check inquiries
1. **Log out** and log back in as the vendor
2. Click **"Vendor dashboard"**
3. Click **"Inquiries"** tab
4. See all inquiries from buyers
5. Click **"Mark as replied"** to update status

---

## 🎨 Customize (optional)

### Change the site name
Edit `templates/base.html`, line with "RentalBlueprint":
```html
<a href="{% url 'rentals:home' %}" class="... text-xl font-extrabold text-teal-800">
  <i class="fa-solid fa-house-chimney"></i> MyPropertyHub  <!-- Change this -->
</a>
```

### Change the currency symbol
Edit `rental_blueprint_project/settings.py`:
```python
CURRENCY_SYMBOL = "Rs "  # For Pakistan
# or
CURRENCY_SYMBOL = "PKR "
```

### Change the color scheme
The primary color is **teal** (`#0f766e`, `#047857`, `#0d9488`). It's used throughout as `bg-teal-800`, `text-teal-800`, etc.

To change to blue:
1. Find all `bg-teal-` and replace with `bg-blue-`
2. Find all `text-teal-` and replace with `text-blue-`
3. Find all `hover:bg-teal-` and replace with `hover:bg-blue-`

Or hire a designer to make a custom theme.

### Add more fields to listings
1. Open `rentals/models.py`
2. Add a field to the `RentalListing` class:
   ```python
   roof_type = models.CharField(max_length=50, blank=True, choices=[("flat", "Flat"), ("pitched", "Pitched")])
   ```
3. Run:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. Add it to the form in `rentals/forms.py`:
   ```python
   fields = [..., "roof_type"]
   ```
5. Update templates to show it

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
You didn't install dependencies. Run:
```bash
pip install -r requirements.txt
```

### "OperationalError: no such table: rentals_rentallisting"
You didn't migrate. Run:
```bash
python manage.py migrate
```

### Photos not uploading or showing
1. Make sure the `/media/` folder exists (it should)
2. Check that `MEDIA_ROOT` and `MEDIA_URL` are set in `settings.py`
3. Restart the server

### Can't log in with the admin user
Make sure you created it:
```bash
python manage.py createsuperuser
```

### "ALLOWED_HOSTS" error on deployment
Edit `rental_blueprint_project/settings.py`:
```python
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

### Something else is broken
1. Check the error message in the terminal
2. Search it on Google or StackOverflow
3. Post on the Django forum

---

## 📁 Project Structure (quick reference)

```
rental_blueprint_complete/
├── manage.py                      ← Run: python manage.py runserver
├── requirements.txt               ← All dependencies listed here
├── db.sqlite3                     ← Your database (created on migrate)
├── media/                         ← User uploads (photos)
├── static/                        ← CSS, JS (optional, for production)
│
├── rental_blueprint_project/      ← Django config folder
│   ├── settings.py                ← Database, apps, templates, media
│   ├── urls.py                    ← Route all traffic to accounts + rentals
│   ├── wsgi.py                    ← For production deployment
│   └── asgi.py                    ← For async (Channels, etc.)
│
├── accounts/                      ← User auth (register, login, profile)
│   ├── models.py                  ← CustomUser model
│   ├── forms.py                   ← RegisterForm, ProfileForm
│   ├── views.py                   ← register, profile views
│   ├── urls.py                    ← /accounts/register/, /accounts/profile/
│   └── admin.py                   ← Manage users in Django admin
│
├── rentals/                       ← Marketplace (properties, search, bookings)
│   ├── models.py                  ← RentalListing, Review, Booking, Inquiry, etc.
│   ├── forms.py                   ← SearchForm, ListingForm, InquiryForm, etc.
│   ├── views.py                   ← HomePage, PropertyListView, DetailView, etc.
│   ├── urls.py                    ← All marketplace routes
│   ├── admin.py                   ← Manage properties in Django admin
│   ├── context_processors.py      ← Favorites available in all templates
│   └── templatetags/rental_extras.py  ← Filters like |money and |stars
│
└── templates/                     ← HTML files (inherits from base.html)
    ├── base.html                  ← Master layout (navbar, footer, blocks)
    ├── registration/
    │   ├── login.html
    │   └── register.html
    ├── accounts/
    │   └── profile.html
    └── rentals/
        ├── home.html              ← Homepage with hero search
        ├── property_list.html     ← Search results with sidebar filters
        ├── listing_detail.html    ← Property details + booking/inquiry forms
        ├── favorites.html         ← Saved properties grid
        ├── user_dashboard.html    ← Buyer's saved, inquiries, bookings
        ├── vendor_dashboard.html  ← Vendor's metrics and overview
        ├── vendor_properties.html ← Vendor's all listings (edit/delete)
        ├── vendor_inquiries.html  ← Vendor's inquiry inbox
        ├── vendor_requests.html   ← Vendor's booking requests
        ├── listing_form.html      ← Add/edit property form
        ├── property_unavailable.html
        └── partials/              ← Reusable components
            ├── _navbar.html       ← Top navigation
            ├── _card.html         ← Property card (used in grids)
            ├── _field.html        ← Form field (used in all forms)
            ├── _stars.html        ← Star rating display
            ├── _status.html       ← Status badge (replied, confirmed, etc.)
            ├── _vendor_nav.html   ← Vendor dashboard tabs
            ├── _auth_shell.html   ← Login/register layout
            └── _messages.html     ← Success/error messages
```

---

## 📚 Next Steps

**After you confirm it works:**
1. Customize the look (colors, logo, text)
2. Add more fields to listings if needed (like "furnished", "utilities included", etc.)
3. Set up email notifications (vendor gets email when inquiry arrives)
4. Deploy to a real server (Heroku, PythonAnywhere, AWS, etc.)

**Learn more:**
- Django docs: https://docs.djangoproject.com/
- Tailwind docs: https://tailwindcss.com/docs
- SQLite to PostgreSQL (for production): https://devcenter.heroku.com/articles/heroku-postgresql

---

**You're ready! Run `python manage.py runserver` and start exploring. 🚀**
