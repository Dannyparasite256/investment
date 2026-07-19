from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_ticket_realtime_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportticket',
            name='user_in_chat',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='staff_in_chat',
            field=models.BooleanField(default=False),
        ),
    ]
