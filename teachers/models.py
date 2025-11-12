from django.db import models

# Create your models here.

class Teacher(models.Model):
    # Tous les choix statiques ont été supprimés pour éviter les doublons
    # Les choix sont désormais gérés dynamiquement via les tables de référence dans reglage
    
    photo = models.ImageField(upload_to='teacher_photos/', null=True, blank=True)
    matricule = models.CharField(max_length=20, unique=True)
    nom_complet = models.CharField(max_length=100)
    fonction = models.CharField(max_length=50)
    grade = models.CharField(max_length=50, default='ASS1')
    section = models.CharField(max_length=50, null=True, blank=True)
    categorie = models.CharField(max_length=25)
    departement = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.matricule} - {self.nom_complet}"
    
    def get_grade_designation(self):
        """Retourne la désignation complète du grade depuis la table Grade"""
        if not self.grade:
            return ''
        try:
            from reglage.models import Grade
            grade_obj = Grade.objects.get(CodeGrade=self.grade)
            return grade_obj.DesignationGrade
        except:
            return self.grade  # Fallback sur le code si la désignation n'existe pas
