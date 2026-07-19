from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0006_chat_feature_pack'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketmessage',
            name='is_voice',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='is_forwarded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='forwarded_from',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forwards',
                to='support.ticketmessage',
            ),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='mentioned_user_ids',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
