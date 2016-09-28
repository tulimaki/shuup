# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2016, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.conf.urls import url

from .views import (
    LoginView, LogoutView, RecoverPasswordCompleteView,
    RecoverPasswordConfirmView, RecoverPasswordSentView, RecoverPasswordView
)

urlpatterns = [
    url(r'^login/$',
        LoginView.as_view(),
        name='login'),
    url(r'^logout/$',
        LogoutView.as_view(),
        name='logout'),
    url(r'^recover-password/$',
        RecoverPasswordView.as_view(),
        name='recover_password'),
    url(r'^recover-password/(?P<uidb64>.+)/(?P<token>.+)/$',
        RecoverPasswordConfirmView.as_view(),
        name='recover_password_confirm'),
    url(r'^recover-password/sent/$',
        RecoverPasswordSentView.as_view(),
        name='recover_password_sent'),
    url(r'^recover-password/complete/$',
        RecoverPasswordCompleteView.as_view(),
        name='recover_password_complete'),
]
