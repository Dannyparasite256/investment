from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_help_text_withdraw_reauth'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='dnd_enabled',
            field=models.BooleanField(
                default=False,
                help_text='Silence push/desktop alerts during DND hours',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='dnd_start',
            field=models.TimeField(
                blank=True,
                help_text='DND start time (local), e.g. 22:00',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='dnd_end',
            field=models.TimeField(
                blank=True,
                help_text='DND end time (local), e.g. 07:00',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='last_vip_tier_slug',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
