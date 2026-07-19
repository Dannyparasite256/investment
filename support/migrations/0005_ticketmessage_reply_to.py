# Generated manually for WhatsApp-style reply quotes

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0004_ticket_in_chat'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketmessage',
            name='reply_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='replies',
                to='support.ticketmessage',
            ),
        ),
    ]
