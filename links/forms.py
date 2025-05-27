from django import forms
from .models import UserAPIKey

# SERVICES list can be defined in views.py or settings.py if it needs to be shared
# For this form, it's fine here if only used for dynamic field creation.
SERVICES_CONFIG = [ # Renamed to avoid conflict if imported elsewhere
    {"key": "psi", "name": "Google PageSpeed Insights"},
    {"key": "uptimerobot", "name": "UptimeRobot"},
    # Add more services here if they need API keys managed via this form
]

class APIKeyForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Dynamically create fields for each service
        for service in SERVICES_CONFIG:
            field_name = f"key_{service['key']}"
            self.fields[field_name] = forms.CharField(
                label=f"{service['name']} API Key",
                required=False, # Keys are not strictly required; empty means remove/don't set
                widget=forms.TextInput(attrs={ # Changed to TextInput for visibility during testing; can be PasswordInput
                    "placeholder": f"Enter your {service['name']} API key",
                    "autocomplete": "new-password", # Prevents browser autofill if desired
                    "class": "form-control",
                })
            )

        # Preload initial values if user and data are not already provided (i.e., for GET requests)
        if user and not self.is_bound: # self.is_bound is True if data is passed (POST)
            user_keys = {uk.service: uk.key for uk in UserAPIKey.objects.filter(user=user)}
            for service in SERVICES_CONFIG:
                field_name = f"key_{service['key']}"
                if service['key'] in user_keys:
                    self.fields[field_name].initial = user_keys[service['key']]