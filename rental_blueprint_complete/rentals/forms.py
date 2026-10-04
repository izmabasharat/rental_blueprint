# rentals/forms.py
from django import forms
from django.core.exceptions import ValidationError

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "text", "id": "id_start_date", "autocomplete": "off",
                                                 "placeholder": "Check-in"}),
            "end_date": forms.DateInput(attrs={"type": "text", "id": "id_end_date", "autocomplete": "off",
                                               "placeholder": "Check-out"}),
        }

    def __init__(self, *args, listing, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing, self.customer = listing, customer

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end:
            # Unsaved instance -> model.clean() (dates + overlap) stays the single source of truth.
            self.instance.listing, self.instance.customer = self.listing, self.customer
            try:
                self.instance.clean()
            except ValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return cleaned


# ======================================================================
# Marketplace forms (added). BookingForm above is unchanged.
# ======================================================================
from .models import AMENITY_CHOICES, Inquiry, ListingImage, RentalListing, Review, validate_image_file

# One shared style so every input looks the same (Tailwind classes).
INPUT = ("w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 "
         "focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-700/30")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Lets one <input type=file multiple> return a list of validated files (pattern from the Django docs)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)] if data else []


class ListingForm(forms.ModelForm):
    amenities = forms.MultipleChoiceField(choices=AMENITY_CHOICES, required=False,
                                          widget=forms.CheckboxSelectMultiple)
    gallery = MultipleFileField(required=False, label="More photos (you can select several)")

    class Meta:
        model = RentalListing
        fields = ["title", "description", "purpose", "property_type", "price_per_day", "sale_price",
                  "city", "area", "location", "bedrooms", "bathrooms", "size_sqft", "amenities",
                  "image", "is_active"]
        labels = {"price_per_day": "Rent price (per day)", "sale_price": "Sale price",
                  "size_sqft": "Size (sq ft)", "is_active": "Published (visible to everyone)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.setdefault("class", INPUT)
        # Required on the form even though the DB allows blanks (older rows).
        for name in ("city", "area", "size_sqft"):
            self.fields[name].required = True
        self.fields["description"].widget.attrs["rows"] = 5
        if self.instance.pk:
            self.initial["amenities"] = [a for a in self.instance.amenities.split(",") if a]
            self.fields["image"].required = False

    def clean_amenities(self):
        return ",".join(self.cleaned_data["amenities"])

    def clean_bedrooms(self):
        v = self.cleaned_data["bedrooms"]
        if v > 50:
            raise forms.ValidationError("That number of bedrooms looks wrong.")
        return v

    def clean_size_sqft(self):
        v = self.cleaned_data["size_sqft"]
        if v is not None and v < 1:
            raise forms.ValidationError("Size must be greater than zero.")
        return v

    def clean_gallery(self):
        files = self.cleaned_data["gallery"]
        if len(files) > 10:
            raise forms.ValidationError("You can upload at most 10 extra photos at a time.")
        for f in files:
            validate_image_file(f)
        return files

    def clean(self):
        cleaned = super().clean()
        # Only the price that matches the purpose is kept.
        if cleaned.get("purpose") == RentalListing.Purpose.SALE:
            cleaned["price_per_day"] = None
            self.instance.price_per_day = None
        elif cleaned.get("purpose") == RentalListing.Purpose.RENT:
            cleaned["sale_price"] = None
            self.instance.sale_price = None
        return cleaned

    def save_gallery(self, listing):
        for f in self.cleaned_data.get("gallery", []):
            ListingImage.objects.create(listing=listing, image=f)


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT
        self.fields["phone"].widget.attrs["placeholder"] = "+92 300 1234567"

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = [c for c in phone if c.isdigit()]
        if len(digits) < 7 or len(digits) > 15 or any(not (c.isdigit() or c in "+-() ") for c in phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean_message(self):
        msg = self.cleaned_data["message"].strip()
        if len(msg) < 10:
            raise forms.ValidationError("Please write at least a short sentence (10+ characters).")
        return msg


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(coerce=int, choices=[(i, str(i)) for i in range(5, 0, -1)],
                                    widget=forms.RadioSelect)

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"comment": forms.Textarea(attrs={"rows": 3, "class": INPUT})}

    def __init__(self, *args, listing, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.listing, self.instance.user = listing, user

    def clean(self):
        cleaned = super().clean()
        try:
            self.instance.clean()        # "only after a completed, confirmed stay" rule lives in the model
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages)
        if Review.objects.filter(listing=self.instance.listing, user=self.instance.user).exists():
            raise forms.ValidationError("You have already reviewed this property.")
        return cleaned


class SearchForm(forms.Form):
    """Reads ?q=&purpose=&type=&min_price=&max_price=&beds=&baths=&sort= from the URL (GET)."""
    SORT_CHOICES = [("newest", "Newest first"), ("price_asc", "Price: low to high"),
                    ("price_desc", "Price: high to low"), ("rating", "Top rated")]

    q = forms.CharField(required=False, max_length=100)
    purpose = forms.ChoiceField(required=False, choices=[("", "Buy or Rent")] + RentalListing.Purpose.choices)
    type = forms.ChoiceField(required=False, choices=[("", "Any type")] + RentalListing.PropertyType.choices)
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    beds = forms.IntegerField(required=False, min_value=0, max_value=50)
    baths = forms.IntegerField(required=False, min_value=0, max_value=50)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("purpose", "type", "sort"):
            self.fields[name].widget.attrs["class"] = "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"

    def clean(self):
        cleaned = super().clean()
        lo, hi = cleaned.get("min_price"), cleaned.get("max_price")
        if lo is not None and hi is not None and lo > hi:
            raise forms.ValidationError("Minimum price cannot be higher than maximum price.")
        return cleaned
