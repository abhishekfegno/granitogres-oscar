from django.conf import settings


def _settings(request):
    return {'settings': settings}


def terms(request):
    return {
        'INR': '₹',
        'DETAIL': 'View',
        'UPDATE': 'Update',
        'REMOVE': 'Remove',
        'LIST': 'View',
        'ADD': 'Create',
    }
