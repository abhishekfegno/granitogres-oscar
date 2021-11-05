import django.dispatch

delivery_picked_up = django.dispatch.Signal(providing_args=('instance', ), )
