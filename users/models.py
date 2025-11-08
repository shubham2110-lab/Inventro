from django.db import models

class UserType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    
class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=150)
    
class User(models.Model):
    first_name = models.CharField(max_length=50)
    age = models.PositiveSmallIntegerField()
    address = models.CharField(max_length=150)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
    )
    type = models.ForeignKey(
        UserType,
        on_delete=models.PROTECT
    )
