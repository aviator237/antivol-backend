# Configuration des tâches planifiées avec django-crontab

Ce projet utilise django-crontab pour gérer les tâches planifiées, notamment la vérification des périodes d'essai des entreprises.

## Tâches planifiées

Les tâches suivantes sont configurées dans le fichier `settings.py` :

1. **Vérification quotidienne des périodes d'essai** (tous les jours à minuit) :
   - Désactive les entreprises dont la période d'essai a expiré et qui n'ont pas souscrit à un abonnement
   - Envoie un email de notification aux administrateurs des entreprises désactivées

2. **Envoi de rappels avant expiration** (tous les jours à 10h du matin) :
   - Envoie un email de rappel aux entreprises dont la période d'essai expire dans 7 jours

## Commandes pour gérer les tâches cron

### Ajouter les tâches au crontab du système

```bash
python manage.py crontab add
```

### Afficher les tâches configurées

```bash
python manage.py crontab show
```

### Supprimer les tâches du crontab

```bash
python manage.py crontab remove
```

### Réinitialiser les tâches (supprimer puis ajouter)

```bash
python manage.py crontab remove
python manage.py crontab add
```

## Logs

Les logs des tâches cron sont enregistrés dans les fichiers suivants :

- `/path/to/media_app/logs/cron_trial_status.log` : Logs de la vérification des périodes d'essai
- `/path/to/media_app/logs/cron_reminders.log` : Logs de l'envoi des rappels

## Exécution manuelle des tâches

Pour exécuter manuellement les tâches cron (à des fins de test) :

```python
from company.cron import check_trial_status, send_trial_expiration_reminders

# Vérifier les périodes d'essai
result = check_trial_status()
print(result)

# Envoyer des rappels
result = send_trial_expiration_reminders()
print(result)
```

## Dépannage

Si les tâches cron ne s'exécutent pas comme prévu :

1. Vérifiez que le service cron est en cours d'exécution sur votre système
2. Vérifiez les permissions du fichier crontab
3. Vérifiez les logs du système pour les erreurs cron
4. Exécutez manuellement les tâches pour vérifier qu'elles fonctionnent correctement
