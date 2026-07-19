from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_message_receipts'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportticket',
            name='user_typing_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='staff_typing_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='user_last_seen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='staff_last_seen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
