import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chargehoraire.settings')
django.setup()

from courses.models import Course
from django.db.models import Count

# Trouver les doublons
doublons = Course.objects.values('code_ue').annotate(count=Count('id')).filter(count__gt=1)
print('Doublons trouvés:')
for d in doublons:
    print(f'  {d["code_ue"]}: {d["count"]} occurrences')

# Supprimer les doublons (garder le premier)
for d in doublons:
    code_ue = d['code_ue']
    courses = Course.objects.filter(code_ue=code_ue).order_by('id')
    premier = courses.first()
    doublons_a_supprimer = courses.exclude(id=premier.id)
    print(f'Suppression de {doublons_a_supprimer.count()} doublons pour {code_ue}')
    doublons_a_supprimer.delete()

print('Nettoyage terminé')
