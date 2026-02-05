from django.db import models

# Create your models here.

class Course(models.Model):
    organisation = models.ForeignKey('accounts.Organisation', on_delete=models.CASCADE, related_name='courses', verbose_name='Organisation', null=True, blank=True)
    CLASSE_CHOICES = [
        ('L1', 'L1'),
        ('L2', 'L2'),
        ('L3', 'L3'),
        ('M1', 'M1'),
        ('M2', 'M2'),
    ]
    
    SEMESTRE_CHOICES = [
        ('S1', 'S1'),
        ('S2', 'S2'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('Informatique', 'Informatique'),
        ('Physique', 'Physique'),
        ('Chimie', 'Chimie'),
        ('Biologie', 'Biologie'),
        ('SCAD', 'SCAD'),
        ('Histoire', 'Histoire'),
        ('Anglais', 'Anglais'),
        ('Français', 'Français'),
        ('Mathématique', 'Mathématique'),
        ('Agrovet', 'Agrovet'),
    ]
    
    code_ue = models.CharField(max_length=20, unique=True)
    intitule_ue = models.CharField(max_length=200)
    intitule_ec = models.CharField(max_length=200, blank=True, null=True)
    credit = models.DecimalField(max_digits=5, decimal_places=2)  # Accepte les décimales (ex: 3.5)
    cmi = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='CMI')  # Cours Magistral Intégré
    td_tp = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='TD+TP')  # Travaux Dirigés + Travaux Pratiques
    
    # Champs avec valeurs dynamiques
    classe = models.CharField(max_length=100)
    semestre = models.CharField(max_length=20)
    departement = models.CharField(max_length=100)
    section = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.code_ue} - {self.intitule_ue}"

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['code_ue']
