from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_notification_support_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='category',
            field=models.CharField(
                choices=[
                    ('system', 'System'),
                    ('deposit', 'Deposit'),
                    ('withdrawal', 'Withdrawal'),
                    ('investment', 'Investment'),
                    ('earning', 'Earning'),
                    ('kyc', 'KYC'),
                    ('security', 'Security'),
                    ('referral', 'Referral'),
                    ('announcement', 'Announcement'),
                    ('support', 'Support'),
                    ('vip', 'VIP'),
                ],
                default='system',
                max_length=20,
            ),
        ),
    ]
