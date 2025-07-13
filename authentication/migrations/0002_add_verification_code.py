# Generated manually for adding verification code

from django.db import migrations, models
import random

def generate_verification_code():
    """Génère un code de vérification à 6 chiffres"""
    return str(random.randint(100000, 999999))

def populate_verification_codes(apps, schema_editor):
    """Ajoute des codes de vérification aux enregistrements existants"""
    EmailVerification = apps.get_model('authentication', 'EmailVerification')
    for verification in EmailVerification.objects.all():
        verification.verification_code = generate_verification_code()
        verification.save()

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailverification',
            name='verification_code',
            field=models.CharField(default='000000', max_length=6),
            preserve_default=False,
        ),
        migrations.RunPython(populate_verification_codes),
    ]
