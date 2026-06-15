from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0015_userprofile_referral_code_userprofile_referred_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phoneverificationrequest",
            name="pin_id",
            field=models.CharField(max_length=34),
        ),
    ]
