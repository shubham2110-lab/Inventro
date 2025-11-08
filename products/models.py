from django.db import models

class ItemCategory(models.Model):
    name = models.CharField(max_length=50)


class Item(models.Model):
    SKU = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    in_stock = models.IntegerField()
    in_use = models.IntegerField()
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT
    )