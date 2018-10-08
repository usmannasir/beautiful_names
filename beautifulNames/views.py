# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import HttpResponse

# Create your views here.

def beautifulNames(request):
    return HttpResponse('This plugin provides beautiful names for your Packages, Databases and FTP Accounts.')
