# rentals/models.py
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Avg, Q
from django.urls import reverse


AMENITY_CHOICES = [
    ("parking", "Parking"),
    ("garden", "Garden / Lawn"),
    ("security", "24/7 Security"),
    ("gas", "Gas supply"),
    ("electricity", "Electricity backup"),
    ("ac", "Air conditioning"),
    ("furnished", "Furnished"),
    ("internet", "Internet / WiFi"),
    ("elevator", "Elevator"),
    ("gym", "Gym"),
    ("pool", "Swimming pool"),
    ("balcony", "Balcony"),
]


def validate_image_file(f):
    """Reject non-image extensions and files over 5 MB (ImageField already checks it is a real image)."""
    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise ValidationError("Only JPG, PNG or WEBP images are allowed.")
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("Each image must be 5 MB or smaller.")


class RentalListing(models.Model):
    class Purpose(models.TextChoices):
        RENT = "RENT", "Rent"
        SALE = "SALE", "Buy"

    class PropertyType(models.TextChoices):
        HOUSE = "HOUSE", "House"
        APARTMENT = "APARTMENT", "Apartment / Flat"
        ROOM = "ROOM", "Room"
        PLOT = "PLOT", "Plot / Land"
        COMMERCIAL = "COMMERCIAL", "Shop / Office"

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
        limit_choices_to={"role": "VENDOR"},
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    # Rent price (existing field). Now optional because SALE listings use sale_price instead.
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(Decimal("0.01"))])
    location = models.CharField("Address / location", max_length=200, db_index=True)
    image = models.ImageField("Cover image", upload_to="listings/%Y/%m/", validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ---- marketplace fields (added) ----
    purpose = models.CharField(max_length=4, choices=Purpose.choices, default=Purpose.RENT, db_index=True)
    property_type = models.CharField(max_length=12, choices=PropertyType.choices, default=PropertyType.HOUSE, db_index=True)
    sale_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                     validators=[MinValueValidator(Decimal("0.01"))])
    city = models.CharField(max_length=100, blank=True, db_index=True)
    area = models.CharField(max_length=100, blank=True)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    size_sqft = models.PositiveIntegerField("Size (sq ft)", null=True, blank=True)
    amenities = models.CharField(max_length=300, blank=True, help_text="Comma-separated amenity keys.")
    is_featured = models.BooleanField(default=False, help_text="Show on the homepage 'Featured' section.")
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("rentals:detail", kwargs={"pk": self.pk})

    def clean(self):
        if self.purpose == self.Purpose.RENT and not self.price_per_day:
            raise ValidationError({"price_per_day": "Enter the rent price."})
        if self.purpose == self.Purpose.SALE and not self.sale_price:
            raise ValidationError({"sale_price": "Enter the sale price."})

    @property
    def average_rating(self):
        return self.reviews.aggregate(avg=Avg("rating"))["avg"]

    @property
    def is_for_rent(self):
        return self.purpose == self.Purpose.RENT

    @property
    def price(self):
        return self.price_per_day if self.is_for_rent else self.sale_price

    @property
    def amenity_list(self):
        labels = dict(AMENITY_CHOICES)
        return [labels[k] for k in self.amenities.split(",") if k in labels]

    @property
    def location_display(self):
        parts = [p for p in (self.area, self.city) if p]
        return ", ".join(parts) or self.location

    def is_available(self, start: date, end: date, exclude_booking_id=None) -> bool:
        qs = Booking.objects.overlapping(self, start, end)
        if exclude_booking_id:
            qs = qs.exclude(pk=exclude_booking_id)
        return not qs.exists()

    def quote(self, start: date, end: date) -> Decimal:
        return self.price_per_day * (end - start).days


class ListingImage(models.Model):
    """Extra gallery photos. The cover photo stays in RentalListing.image."""
    listing = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="listings/gallery/%Y/%m/", validators=[validate_image_file])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "listing"], name="one_favorite_per_user_listing")]


class Inquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        REPLIED = "REPLIED", "Replied"

    listing = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name="inquiries")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries")
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    message = models.TextField(max_length=2000)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.NEW, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

    def __str__(self):
        return f"{self.name} about {self.listing}"


# ---------------------------------------------------------------- Booking ---

class BookingQuerySet(models.QuerySet):
    ACTIVE = ("PENDING", "CONFIRMED")

    def active(self):
        return self.filter(status__in=self.ACTIVE)

    def overlapping(self, listing, start, end):
        """
        Bookings that block [start, end). end_date is the CHECK-OUT day and is
        exclusive, so back-to-back stays (A checks out the day B checks in) are allowed.
        Two ranges overlap  <=>  existing.start < new.end  AND  existing.end > new.start
        """
        return self.active().filter(listing=listing, start_date__lt=end, end_date__gt=start)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    listing = models.ForeignKey(RentalListing, on_delete=models.PROTECT, related_name="bookings")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField(help_text="Check-out day (not charged, not blocked).")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["listing", "start_date", "end_date"])]
        constraints = [
            models.CheckConstraint(condition=Q(end_date__gt=models.F("start_date")), name="booking_end_after_start"),
        ]
        # OPTIONAL hard guarantee on PostgreSQL (needs BtreeGistExtension() in a migration):
        #   from django.contrib.postgres.constraints import ExclusionConstraint
        #   from django.contrib.postgres.fields import RangeOperators
        #   from django.db.models import Func, F, Q
        #   ExclusionConstraint(
        #       name="no_overlapping_active_bookings",
        #       expressions=[
        #           ("listing", RangeOperators.EQUAL),
        #           (Func(F("start_date"), F("end_date"), function="daterange"), RangeOperators.OVERLAPS),
        #       ],
        #       condition=Q(status__in=["PENDING", "CONFIRMED"]),
        #   )

    def __str__(self):
        return f"{self.listing} | {self.start_date} to {self.end_date} ({self.status})"

    @property
    def nights(self):
        return (self.end_date - self.start_date).days

    # -- validation ---------------------------------------------------------
    def clean(self):
        if not (self.start_date and self.end_date and self.listing_id):
            return
        if self.end_date <= self.start_date:
            raise ValidationError({"end_date": "Check-out must be after check-in."})
        if self.pk is None and self.start_date < date.today():
            raise ValidationError({"start_date": "Check-in cannot be in the past."})
        if self.status in BookingQuerySet.ACTIVE:
            clash = Booking.objects.overlapping(self.listing, self.start_date, self.end_date).exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError("These dates are no longer available for this listing.")

    def save(self, *args, **kwargs):
        self.total_price = self.listing.quote(self.start_date, self.end_date)
        super().save(*args, **kwargs)

    # -- race-safe creation -------------------------------------------------
    @classmethod
    def create_safely(cls, *, listing, customer, start_date, end_date):
        """
        Serialises concurrent requests per listing by locking the listing row,
        then validates and inserts inside the same transaction.
        Needs row locks (PostgreSQL/MySQL); SQLite ignores select_for_update.
        """
        with transaction.atomic():
            RentalListing.objects.select_for_update().get(pk=listing.pk)
            booking = cls(listing=listing, customer=customer, start_date=start_date, end_date=end_date)
            booking.full_clean(exclude=["total_price"])
            booking.save()
            return booking

    def set_status_safely(self, new_status):
        with transaction.atomic():
            RentalListing.objects.select_for_update().get(pk=self.listing_id)
            self.status = new_status
            self.full_clean(exclude=["total_price"])   # re-checks overlap when confirming
            self.save(update_fields=["status"])


# ----------------------------------------------------------------- Review ---

class Review(models.Model):
    listing = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["listing", "user"], name="one_review_per_user_per_listing")]

    def clean(self):
        # Only guests with a finished, confirmed stay may review.
        if self.listing_id and self.user_id and not Booking.objects.filter(
            listing=self.listing, customer=self.user, status="CONFIRMED", end_date__lte=date.today()
        ).exists():
            raise ValidationError("You can review a listing after completing a confirmed stay.")

    def __str__(self):
        return f"{self.listing} - {self.rating} stars by {self.user}"
