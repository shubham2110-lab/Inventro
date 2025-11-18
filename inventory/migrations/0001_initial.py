# Generated for local dev to create the InventoryItem table up-front.
from django.db import migrations, models
import django.conf

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(blank=True, max_length=255)),
                ('quantity', models.IntegerField(default=0)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='inventory_items_created', to='auth.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='inventory_items_updated', to='auth.user')),
            ],
            options={'ordering': ['name']},
        ),
    ]
