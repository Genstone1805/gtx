# Generated migration for adding balance fields to UserProfile

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_userprofile_has_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='pending_balance',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                default=Decimal('0.00'),
                help_text="Total amount from orders with 'Pending' status (awaiting admin approval)"
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='withdrawable_balance',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                default=Decimal('0.00'),
                help_text="Total amount from orders with 'Approved' status (available for withdrawal)"
            ),
        ),
    ]
