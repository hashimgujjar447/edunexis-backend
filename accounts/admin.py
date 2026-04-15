from django.contrib import admin
from .models import Account,UserToken

# Register your models here.

admin.site.register(Account)
admin.site.register(UserToken)
