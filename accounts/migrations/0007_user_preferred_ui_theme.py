from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_user_timezone_login_geo'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferred_ui_theme',
            field=models.CharField(
                choices=[
                    ('classic', 'Default Theme'),
                    ('premium', 'Premium Investment Theme'),
                ],
                default='classic',
                help_text='Visual design system: classic glass or premium investment UI',
                max_length=16,
            ),
        ),
    ]
