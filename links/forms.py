from django import forms
from .models import UserAPIKey

SERVICES = [
    {"key": "psi", "name": "Google PageSpeed Insights"},
    {"key": "uptimerobot", "name": "UptimeRobot"},
]

class APIKeyForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        for service in SERVICES:
            key = service["key"]
            name = service["name"]
            self.fields[f"key_{key}"] = forms.CharField(
                label=f"{name} API Key",
                required=False,
                widget=forms.PasswordInput(attrs={
                    "placeholder": f"Enter your {name} API key",
                    "autocomplete": "off",
                    "class": "form-control",
                })
            )
        # Preload initial values if user is provided
        if user:
            user_keys = {k.service: k for k in UserAPIKey.objects.filter(user=user)}
            for service in SERVICES:
                key = service["key"]
                if key in user_keys:
                    self.fields[f"key_{key}"].initial = user_keys[key].key 