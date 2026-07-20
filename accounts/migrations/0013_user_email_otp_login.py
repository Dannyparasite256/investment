from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_user_dnd_and_vip_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_otp_login',
            field=models.BooleanField(
                default=True,
                help_text='Require a one-time email code after password login (when TOTP 2FA is off)',
            ),
        ),
    ]
