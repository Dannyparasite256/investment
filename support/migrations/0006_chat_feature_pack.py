from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0005_ticketmessage_reply_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportticket',
            name='muted_by_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='muted_by_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='sla_due_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='first_response_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='pinned_by_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='pinned_by_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='is_starred',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
