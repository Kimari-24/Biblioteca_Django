from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
    path('', include('features.accounts.urls')),
    path('books/', include('features.books.urls')),
    path('loans/', include('features.loans.urls')),
    path('dashboard/', include('features.dashboard.urls')),
]
