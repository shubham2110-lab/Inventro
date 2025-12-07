from django.contrib import admin
from .models import Profile, Company


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass