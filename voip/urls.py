# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path('payment/notify', views.handle_payment_notify, name='handle_payment_notify'),
]