from django.contrib import admin
from .models import User, Company, UserType


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass