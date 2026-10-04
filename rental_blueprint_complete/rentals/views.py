# rentals/views.py
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db.models import Avg, Case, Count, DecimalField, F, Q, Sum, When
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from .forms import BookingForm, InquiryForm, ListingForm, ReviewForm, SearchForm
from .models import Booking, Favorite, Inquiry, ListingImage, RentalListing, Review


# ------------------------------------------------------- Listing detail ------

class RentalListingDetailView(DetailView):
    model = RentalListing
    template_name = "rentals/listing_detail.html"
    context_object_name = "listing"

    def get_queryset(self):
        return (RentalListing.objects
                .select_related("vendor").prefetch_related("reviews__user", "images"))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_active and request.user.pk != self.object.vendor_id:
            return render(request, "rentals/property_unavailable.html", status=404)
        if request.user.pk != self.object.vendor_id:      # count views from everyone except the owner
            RentalListing.objects.filter(pk=self.object.pk).update(view_count=F("view_count") + 1)
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        listing = self.object
        ctx["form"] = kwargs.get("form") or self._blank_form()
        # Ranges the date picker greys out (end is exclusive, so a check-out day stays selectable as check-in).
        ctx["blocked_ranges"] = [
            {"from": b.start_date.isoformat(), "to": b.end_date.isoformat()}
            for b in Booking.objects.active().filter(listing=listing, end_date__gte=date.today())
        ]
        ctx["reviews"] = listing.reviews.all()[:10]

        # ---- marketplace additions ----
        stats = listing.reviews.aggregate(avg=Avg("rating"), n=Count("id"))
        ctx["avg_rating"], ctx["review_count"] = stats["avg"], stats["n"]
        ctx["gallery"] = list(listing.images.all())
        ctx["amenities"] = listing.amenity_list
        ctx["similar"] = (_with_rating(RentalListing.objects.filter(is_active=True, purpose=listing.purpose)
                                       .exclude(pk=listing.pk)
                                       .filter(Q(city__iexact=listing.city) | Q(property_type=listing.property_type))
                                       .select_related("vendor"))[:3])
        user = self.request.user
        ctx["inquiry_form"] = kwargs.get("inquiry_form") or InquiryForm(initial={
            "name": (user.get_full_name() or user.username) if user.is_authenticated else "",
            "email": user.email if user.is_authenticated else ""})
        ctx["is_owner"] = user.is_authenticated and user.pk == listing.vendor_id
        can_review = False
        if user.is_authenticated and not ctx["is_owner"]:
            can_review = (not listing.reviews.filter(user=user).exists() and Booking.objects.filter(
                listing=listing, customer=user, status="CONFIRMED", end_date__lte=date.today()).exists())
        ctx["can_review"] = can_review
        ctx["review_form"] = kwargs.get("review_form") or (
            ReviewForm(listing=listing, user=user) if can_review else None)
        ctx["is_favorite"] = user.is_authenticated and Favorite.objects.filter(user=user, listing=listing).exists()
        return ctx

    def _blank_form(self):
        user = self.request.user if self.request.user.is_authenticated else None
        return BookingForm(listing=self.object, customer=user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if request.user.pk == self.object.vendor_id:
            messages.error(request, "You can't book your own listing.")
            return redirect(self.object)
        if not self.object.is_active:
            messages.error(request, "This property is no longer available.")
            return redirect(self.object)
        if not self.object.is_for_rent:
            messages.error(request, "This property is for sale. Send the agent an inquiry instead.")
            return redirect(self.object)

        form = BookingForm(request.POST, listing=self.object, customer=request.user)
        if form.is_valid():
            try:
                booking = Booking.create_safely(
                    listing=self.object, customer=request.user,
                    start_date=form.cleaned_data["start_date"], end_date=form.cleaned_data["end_date"],
                )
            except ValidationError as exc:      # lost a race between the form check and the insert
                form.add_error(None, exc.messages)
            else:
                messages.success(request, f"Request sent: {booking.nights} nights, total {booking.total_price}.")
                return redirect(self.object)
        return self.render_to_response(self.get_context_data(form=form))


def price_quote(request, pk):
    """GET /listings/<pk>/quote/?start=YYYY-MM-DD&end=YYYY-MM-DD -> live price + availability."""
    listing = get_object_or_404(RentalListing, pk=pk, is_active=True, purpose="RENT")
    start, end = parse_date(request.GET.get("start", "")), parse_date(request.GET.get("end", ""))
    if not (start and end) or end <= start:
        return JsonResponse({"ok": False, "error": "Choose a check-out after check-in."}, status=400)
    return JsonResponse({
        "ok": True,
        "available": listing.is_available(start, end),
        "nights": (end - start).days,
        "total": str(listing.quote(start, end)),
    })


# ------------------------------------------------------ Vendor dashboard -----

class VendorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_vendor


class VendorDashboardView(VendorRequiredMixin, TemplateView):
    template_name = "rentals/vendor_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mine = Booking.objects.filter(listing__vendor=self.request.user).select_related("listing", "customer")
        ctx["listings"] = (RentalListing.objects.filter(vendor=self.request.user)
                           .annotate(pending_count=Count("bookings", filter=Q(bookings__status="PENDING"))))
        ctx["pending_requests"] = mine.filter(status="PENDING").order_by("start_date")
        ctx["upcoming"] = mine.filter(status="CONFIRMED", end_date__gte=date.today()).order_by("start_date")
        # ---- marketplace additions ----
        ctx["stats"] = {
            "listings": ctx["listings"].count(),
            "active": ctx["listings"].filter(is_active=True).count(),
            "new_inquiries": Inquiry.objects.filter(listing__vendor=self.request.user, status="NEW").count(),
            "pending": ctx["pending_requests"].count(),
            "views": ctx["listings"].aggregate(v=Sum("view_count"))["v"] or 0,
            "leads": (Inquiry.objects.filter(listing__vendor=self.request.user).count()
                      + Booking.objects.filter(listing__vendor=self.request.user).count()),
        }
        ctx["active_tab"] = "overview"
        return ctx


class BookingDecisionView(VendorRequiredMixin, View):
    """POST /dashboard/bookings/<pk>/<approve|reject>/ - vendors can only act on their own listings' bookings."""
    ACTIONS = {"approve": Booking.Status.CONFIRMED, "reject": Booking.Status.CANCELLED}

    def post(self, request, pk, action):
        if action not in self.ACTIONS:
            return redirect("rentals:dashboard")
        booking = get_object_or_404(Booking, pk=pk, listing__vendor=request.user, status=Booking.Status.PENDING)
        try:
            booking.set_status_safely(self.ACTIONS[action])
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Booking approved." if action == "approve" else "Booking rejected.")
        return redirect("rentals:dashboard")


# ======================================================================
# Marketplace views (added). Everything above is your original logic.
# ======================================================================

def _with_rating(qs):
    """Adds avg_rating, review_count and a comparable 'effective_price' to a listing queryset."""
    return qs.annotate(
        avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews", distinct=True),
        effective_price=Case(When(purpose="SALE", then=F("sale_price")), default=F("price_per_day"),
                             output_field=DecimalField(max_digits=14, decimal_places=2)),
    )


def _public_listings():
    return _with_rating(RentalListing.objects.filter(is_active=True).select_related("vendor"))


def _safe_next(request, fallback):
    nxt = request.POST.get("next") or request.GET.get("next") or ""
    ok = url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return nxt if ok else fallback


# ----------------------------------------------------------------- Home -----

class HomeView(TemplateView):
    template_name = "rentals/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = _public_listings()
        featured = list(qs.filter(is_featured=True)[:6])
        ctx["featured"] = featured or list(qs.order_by("-avg_rating", "-created_at")[:6])
        ctx["recent"] = list(qs.order_by("-created_at")[:8])
        ctx["popular_cities"] = (RentalListing.objects.filter(is_active=True).exclude(city="")
                                 .values("city").annotate(n=Count("id")).order_by("-n")[:6])
        counts = dict(RentalListing.objects.filter(is_active=True).values_list("property_type")
                      .annotate(n=Count("id")))
        ctx["categories"] = [(value, label, counts.get(value, 0)) for value, label in RentalListing.PropertyType.choices]
        ctx["form"] = SearchForm()
        return ctx


# --------------------------------------------------------------- Search -----

class PropertyListView(ListView):
    template_name = "rentals/property_list.html"
    context_object_name = "listings"
    paginate_by = 12

    def get_queryset(self):
        self.form = SearchForm(self.request.GET or None)
        qs = _public_listings()
        if not (self.form.is_bound and self.form.is_valid()):
            return qs.order_by("-created_at")
        d = self.form.cleaned_data
        self._remember_search()
        if d["q"]:
            q = d["q"].strip()
            qs = qs.filter(Q(city__icontains=q) | Q(area__icontains=q) | Q(location__icontains=q) | Q(title__icontains=q))
        if d["purpose"]:
            qs = qs.filter(purpose=d["purpose"])
        if d["type"]:
            qs = qs.filter(property_type=d["type"])
        if d["min_price"] is not None:
            qs = qs.filter(effective_price__gte=d["min_price"])
        if d["max_price"] is not None:
            qs = qs.filter(effective_price__lte=d["max_price"])
        if d["beds"] is not None:
            qs = qs.filter(bedrooms__gte=d["beds"])
        if d["baths"] is not None:
            qs = qs.filter(bathrooms__gte=d["baths"])
        order = {"price_asc": ["effective_price"], "price_desc": ["-effective_price"],
                 "rating": [F("avg_rating").desc(nulls_last=True), "-created_at"]}.get(d["sort"], ["-created_at"])
        return qs.order_by(*order)

    def _remember_search(self):
        """Keeps the last 5 searches in the session (shown on the user dashboard). No database needed."""
        params = self.request.GET.copy()
        for key in ("page", "sort"):
            params.pop(key, None)
        if not any(params.values()):
            return
        label = " · ".join(v for v in (params.get("q"), params.get("purpose"), params.get("type")) if v)
        entry = {"label": label, "qs": params.urlencode()}
        recent = [e for e in self.request.session.get("recent_searches", []) if e["qs"] != entry["qs"]]
        self.request.session["recent_searches"] = ([entry] + recent)[:5]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        ctx["city_label"] = (self.form.cleaned_data.get("q") if self.form.is_bound and self.form.is_valid() else "")
        ctx["total"] = ctx["paginator"].count
        return ctx


# ------------------------------------------------------------ Favourites ----

@require_POST
@login_required
def toggle_favorite(request, pk):
    listing = get_object_or_404(RentalListing, pk=pk, is_active=True)
    fav, created = Favorite.objects.get_or_create(user=request.user, listing=listing)
    if created:
        messages.success(request, "Property saved successfully.")
    else:
        fav.delete()
        messages.info(request, "Property removed from your saved list.")
    return redirect(_safe_next(request, listing.get_absolute_url()))


class FavoritesView(LoginRequiredMixin, ListView):
    template_name = "rentals/favorites.html"
    context_object_name = "listings"

    def get_queryset(self):
        ids = Favorite.objects.filter(user=self.request.user).values_list("listing_id", flat=True)
        return _public_listings().filter(pk__in=ids)


# ------------------------------------------------- Inquiry & reviews ---------

def _render_detail(request, listing, **forms):
    view = RentalListingDetailView()
    view.setup(request, pk=listing.pk)
    view.object = listing
    return view.render_to_response(view.get_context_data(**forms))


@require_POST
@login_required
def send_inquiry(request, pk):
    listing = get_object_or_404(RentalListing, pk=pk, is_active=True)
    if request.user.pk == listing.vendor_id:
        messages.error(request, "You can't send an inquiry on your own property.")
        return redirect(listing)
    form = InquiryForm(request.POST)
    if form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.listing, inquiry.sender = listing, request.user
        inquiry.save()
        messages.success(request, "Inquiry submitted successfully. The agent will contact you soon.")
        return redirect(listing)
    messages.error(request, "Invalid form data. Please check the inquiry form.")
    return _render_detail(request, listing, inquiry_form=form)


@require_POST
@login_required
def submit_review(request, pk):
    listing = get_object_or_404(RentalListing, pk=pk, is_active=True)
    form = ReviewForm(request.POST, listing=listing, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Thanks! Your review has been posted.")
        return redirect(listing)
    messages.error(request, "Your review could not be saved.")
    return _render_detail(request, listing, review_form=form)


# ------------------------------------------------------- User dashboard ------

@login_required
def after_login(request):
    """LOGIN_REDIRECT_URL target: vendors -> vendor dashboard, everyone else -> personal dashboard."""
    return redirect("rentals:dashboard" if request.user.is_vendor else "rentals:account")


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "rentals/user_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["favorites"] = Favorite.objects.filter(user=u).select_related("listing")[:6]
        ctx["favorite_count"] = Favorite.objects.filter(user=u).count()
        ctx["inquiries"] = Inquiry.objects.filter(sender=u).select_related("listing")
        ctx["bookings"] = Booking.objects.filter(customer=u).select_related("listing")
        return ctx


@require_POST
@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user, status=Booking.Status.PENDING)
    booking.set_status_safely(Booking.Status.CANCELLED)
    messages.success(request, "Your request was cancelled.")
    return redirect("rentals:account")


# ----------------------------------------------- Vendor: property CRUD -------

class VendorPropertiesView(VendorRequiredMixin, TemplateView):
    template_name = "rentals/vendor_properties.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["listings"] = (RentalListing.objects.filter(vendor=self.request.user)
                           .annotate(pending_count=Count("bookings", filter=Q(bookings__status="PENDING"), distinct=True),
                                     inquiry_count=Count("inquiries", distinct=True)))
        ctx["active_tab"] = "properties"
        return ctx


class _ListingFormMixin(VendorRequiredMixin):
    model = RentalListing
    form_class = ListingForm
    template_name = "rentals/listing_form.html"

    def get_queryset(self):                      # vendors can only ever load their OWN listings
        return RentalListing.objects.filter(vendor=self.request.user)

    def form_valid(self, form):
        listing = form.save(commit=False)
        listing.vendor = self.request.user
        listing.save()
        form.save_gallery(listing)
        remove = self.request.POST.getlist("delete_images")
        if remove:
            ListingImage.objects.filter(listing=listing, pk__in=[i for i in remove if i.isdigit()]).delete()
        messages.success(self.request, "Property saved successfully.")
        return redirect("rentals:vendor_properties")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid form data. Please fix the highlighted fields.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = "add"
        return ctx


from django.views.generic import CreateView, UpdateView  # noqa: E402  (kept near its only users)


class ListingCreateView(_ListingFormMixin, CreateView):
    pass


class ListingUpdateView(_ListingFormMixin, UpdateView):
    pass


@require_POST
@login_required
def listing_toggle_active(request, pk):
    listing = get_object_or_404(RentalListing, pk=pk, vendor=request.user)
    listing.is_active = not listing.is_active
    listing.save(update_fields=["is_active"])
    messages.success(request, "Property is now live." if listing.is_active else "Property hidden from search.")
    return redirect("rentals:vendor_properties")


@require_POST
@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(RentalListing, pk=pk, vendor=request.user)
    if listing.bookings.exists():                # Booking.listing is PROTECT, so deleting would crash
        messages.error(request, "This property has booking history, so it can't be deleted. Deactivate it instead.")
    else:
        listing.delete()
        messages.success(request, "Property deleted.")
    return redirect("rentals:vendor_properties")


# ------------------------------------- Vendor: inquiries & booking requests --

class VendorInquiriesView(VendorRequiredMixin, TemplateView):
    template_name = "rentals/vendor_inquiries.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["inquiries"] = Inquiry.objects.filter(listing__vendor=self.request.user).select_related("listing")
        ctx["active_tab"] = "inquiries"
        return ctx


@require_POST
@login_required
def inquiry_mark_replied(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk, listing__vendor=request.user)
    inquiry.status = Inquiry.Status.REPLIED
    inquiry.save(update_fields=["status"])
    messages.success(request, "Marked as replied.")
    return redirect("rentals:vendor_inquiries")


class VendorRequestsView(VendorRequiredMixin, TemplateView):
    template_name = "rentals/vendor_requests.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bookings"] = (Booking.objects.filter(listing__vendor=self.request.user)
                           .select_related("listing", "customer"))
        ctx["active_tab"] = "requests"
        return ctx
