import os

from .base_dir import BASE_DIR

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates'),
]

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lib.context_processors._settings',
                'lib.context_processors.terms',
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.apps.customer.notifications.context_processors.notifications',
                'oscar.core.context_processors.metadata',
            ],
            # 'loaders': [
                # ('django.template.loaders.cached.Loader', [
                #     'django.template.loaders.filesystem.Loader',
                #     'django.template.loaders.app_directories.Loader',
                #     # # 'path.to.custom.Loader',
                # ]),
            # ],
            # 'libraries': {
            # }
        },
    },
]
