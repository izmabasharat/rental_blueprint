# accounts/models.py
# settings.py -> AUTH_USER_MODEL = "accounts.CustomUser"  (set BEFORE the first migrate)
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        VENDOR = "VENDOR", "Vendor"
        CUSTOMER = "CUSTOMER", "Customer"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER, db_index=True)

    @property
    def is_vendor(self) -> bool:
        return self.role == self.Role.VENDOR

    @property
    def is_marketplace_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser
