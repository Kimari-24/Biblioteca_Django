from django.urls import path

from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.all_loans, name='all'),
    path('mine/', views.my_loans, name='mine'),
    path('borrow/<str:book_id>/', views.borrow, name='borrow'),
    path('<str:loan_id>/return/', views.return_loan, name='return'),
    path('<str:loan_id>/cancel/', views.cancel_loan, name='cancel'),
]
