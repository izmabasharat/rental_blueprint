from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class RegisterForm(UserCreationForm):
    """Sign-up. People can choose Customer or Vendor; Admin can never be chosen here."""
    account_type = forms.ChoiceField(
        choices=[(CustomUser.Role.CUSTOMER, "I want to buy / rent a property"),
                 (CustomUser.Role.VENDOR, "I'm an agent / owner and want to list properties")],
        widget=forms.RadioSelect, initial=CustomUser.Role.CUSTOMER)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if name != "account_type":
                f.widget.attrs["class"] = ("w-full rounded-lg border border-slate-300 px-3 py-2 "
                                           "focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-700/30")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["account_type"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")     # role/username are NOT editable here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"] = ("w-full rounded-lg border border-slate-300 px-3 py-2 "
                                       "focus:border-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-700/30")
