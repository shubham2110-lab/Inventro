from django.db import models

class UserType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    
class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=150)
    
class User(models.Model):
    # existing fields...
    first_name = models.CharField(max_length=255)
    age = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    type = models.ForeignKey(UserType, on_delete=models.PROTECT)

    # RBAC roles
    ROLE_ADMIN = "ADMIN"
    ROLE_MANAGER = "MANAGER"
    ROLE_STAFF = "STAFF"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_STAFF, "Staff"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAFF,
        help_text="Role used for access control (RBAC).",
    )

    def __str__(self):
        return self.first_name
