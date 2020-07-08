
import django.dispatch

pincode_changed = django.dispatch.Signal(providing_args=["user", "pincode"])
