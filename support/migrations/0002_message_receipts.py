from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supportticket',
            options={'ordering': ['-updated_at', '-created_at']},
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='ticketmessage',
            name='read_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
