"""
Validators pour détecter les conflits dans les horaires
"""
from .models import ScheduleEntry
from django.core.exceptions import ValidationError


class ScheduleConflictValidator:
    """Classe pour valider les conflits d'horaires"""
    
    @staticmethod
    def check_teacher_conflict(enseignant, jour, creneau, semaine, exclude_id=None):
        """
        Vérifie si un enseignant a déjà un cours au même moment
        
        Args:
            enseignant: Objet Teacher
            jour: str - jour de la semaine (lundi, mardi, etc.)
            creneau: str - code du créneau (AM, PM, etc.)
            semaine: date - date de début de semaine
            exclude_id: int - ID de l'horaire à exclure (pour modification)
            
        Returns:
            tuple: (bool, list) - (has_conflict, conflicting_entries)
        """
        conflicts = ScheduleEntry.objects.filter(
            attribution__matricule=enseignant,
            jour=jour,
            creneau=creneau,
            semaine_debut=semaine
        ).select_related('attribution__code_ue')
        
        if exclude_id:
            conflicts = conflicts.exclude(id=exclude_id)
        
        if conflicts.exists():
            return True, list(conflicts)
        return False, []
    
    @staticmethod
    def check_room_conflict(salle, jour, creneau, semaine, exclude_id=None):
        """
        Vérifie si une salle est déjà occupée au même moment
        
        Args:
            salle: str - code de la salle
            jour: str - jour de la semaine
            creneau: str - code du créneau
            semaine: date - date de début de semaine
            exclude_id: int - ID de l'horaire à exclure
            
        Returns:
            tuple: (bool, list) - (has_conflict, conflicting_entries)
        """
        if not salle:  # Pas de conflit si pas de salle spécifiée
            return False, []
        
        conflicts = ScheduleEntry.objects.filter(
            salle=salle,
            jour=jour,
            creneau=creneau,
            semaine_debut=semaine
        ).select_related('attribution__code_ue', 'attribution__matricule')
        
        if exclude_id:
            conflicts = conflicts.exclude(id=exclude_id)
        
        if conflicts.exists():
            return True, list(conflicts)
        return False, []
    
    @staticmethod
    def check_class_conflict(classe, jour, creneau, semaine, exclude_id=None):
        """
        Vérifie si une classe a déjà un cours au même moment
        
        Args:
            classe: str - code de la classe (L1MI, L2BC, etc.)
            jour: str - jour de la semaine
            creneau: str - code du créneau
            semaine: date - date de début de semaine
            exclude_id: int - ID de l'horaire à exclure
            
        Returns:
            tuple: (bool, list) - (has_conflict, conflicting_entries)
        """
        conflicts = ScheduleEntry.objects.filter(
            attribution__code_ue__classe=classe,
            jour=jour,
            creneau=creneau,
            semaine_debut=semaine
        ).select_related('attribution__code_ue', 'attribution__matricule')
        
        if exclude_id:
            conflicts = conflicts.exclude(id=exclude_id)
        
        if conflicts.exists():
            return True, list(conflicts)
        return False, []
    
    @classmethod
    def validate_schedule_entry(cls, attribution, jour, creneau, semaine, salle=None, exclude_id=None):
        """
        Valide un horaire contre tous les types de conflits
        
        Args:
            attribution: Objet Attribution
            jour: str - jour de la semaine
            creneau: str - code du créneau
            semaine: date - date de début de semaine
            salle: str - code de la salle (optionnel)
            exclude_id: int - ID de l'horaire à exclure (pour modification)
            
        Returns:
            dict: {
                'valid': bool,
                'errors': list of str,
                'warnings': list of str,
                'conflicts': dict
            }
        """
        print(f"\n>>> ScheduleConflictValidator.validate_schedule_entry appelé")
        print(f"    Attribution: {attribution}")
        print(f"    Enseignant: {attribution.matricule}")
        print(f"    Classe: {attribution.code_ue.classe}")
        print(f"    Jour: {jour}")
        print(f"    Créneau: {creneau}")
        print(f"    Semaine: {semaine}")
        print(f"    Salle: {salle}")
        print(f"    Exclude ID: {exclude_id}")
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'conflicts': {}
        }
        
        # 1. Vérifier conflit enseignant (BLOQUANT)
        print(f"\n>>> Vérification conflit enseignant...")
        has_teacher_conflict, teacher_conflicts = cls.check_teacher_conflict(
            attribution.matricule, jour, creneau, semaine, exclude_id
        )
        print(f"    Conflit enseignant? {has_teacher_conflict}")
        if has_teacher_conflict:
            print(f"    Nombre de conflits: {len(teacher_conflicts)}")
        if has_teacher_conflict:
            result['valid'] = False
            conflict = teacher_conflicts[0]
            result['errors'].append(
                f"⚠️ CONFLIT ENSEIGNANT : {attribution.matricule.nom_complet} est déjà programmé(e) "
                f"pour le cours {conflict.attribution.code_ue.code_ue} "
                f"({conflict.attribution.code_ue.intitule_ue}) "
                f"avec la classe {conflict.attribution.code_ue.classe}"
            )
            result['conflicts']['teacher'] = teacher_conflicts
        
        # 2. Vérifier conflit salle (BLOQUANT)
        if salle:
            has_room_conflict, room_conflicts = cls.check_room_conflict(
                salle, jour, creneau, semaine, exclude_id
            )
            if has_room_conflict:
                result['valid'] = False
                conflict = room_conflicts[0]
                result['errors'].append(
                    f"⚠️ CONFLIT SALLE : La salle {salle} est déjà occupée par "
                    f"{conflict.attribution.matricule.nom_complet} "
                    f"pour le cours {conflict.attribution.code_ue.code_ue} "
                    f"({conflict.attribution.code_ue.classe})"
                )
                result['conflicts']['room'] = room_conflicts
        
        # 3. Vérifier conflit classe (BLOQUANT)
        classe = attribution.code_ue.classe
        has_class_conflict, class_conflicts = cls.check_class_conflict(
            classe, jour, creneau, semaine, exclude_id
        )
        if has_class_conflict:
            result['valid'] = False
            conflict = class_conflicts[0]
            result['errors'].append(
                f"⚠️ CONFLIT CLASSE : La classe {classe} a déjà le cours "
                f"{conflict.attribution.code_ue.code_ue} "
                f"({conflict.attribution.code_ue.intitule_ue}) "
                f"avec {conflict.attribution.matricule.nom_complet}"
            )
            result['conflicts']['class'] = class_conflicts
        
        return result
    
    @classmethod
    def get_conflicts_for_week(cls, semaine):
        """
        Récupère tous les conflits pour une semaine donnée
        
        Args:
            semaine: date - date de début de semaine
            
        Returns:
            dict: Rapport complet des conflits de la semaine
        """
        entries = ScheduleEntry.objects.filter(
            semaine_debut=semaine
        ).select_related('attribution__matricule', 'attribution__code_ue')
        
        conflicts_report = {
            'teacher_conflicts': [],
            'room_conflicts': [],
            'class_conflicts': [],
            'total_conflicts': 0
        }
        
        # Vérifier chaque entrée
        checked_combinations = set()
        
        for entry in entries:
            # Créer une clé unique pour éviter de vérifier 2 fois la même combinaison
            key = f"{entry.jour}_{entry.creneau}"
            
            if key not in checked_combinations:
                checked_combinations.add(key)
                
                # Vérifier les doublons enseignants
                teacher_entries = entries.filter(
                    attribution__matricule=entry.attribution.matricule,
                    jour=entry.jour,
                    creneau=entry.creneau
                )
                if teacher_entries.count() > 1:
                    conflicts_report['teacher_conflicts'].append({
                        'teacher': entry.attribution.matricule.nom_complet,
                        'jour': entry.jour,
                        'creneau': entry.creneau,
                        'entries': list(teacher_entries)
                    })
                
                # Vérifier les doublons salles
                if entry.salle:
                    room_entries = entries.filter(
                        salle=entry.salle,
                        jour=entry.jour,
                        creneau=entry.creneau
                    )
                    if room_entries.count() > 1:
                        conflicts_report['room_conflicts'].append({
                            'salle': entry.salle,
                            'jour': entry.jour,
                            'creneau': entry.creneau,
                            'entries': list(room_entries)
                        })
                
                # Vérifier les doublons classes
                class_entries = entries.filter(
                    attribution__code_ue__classe=entry.attribution.code_ue.classe,
                    jour=entry.jour,
                    creneau=entry.creneau
                )
                if class_entries.count() > 1:
                    conflicts_report['class_conflicts'].append({
                        'classe': entry.attribution.code_ue.classe,
                        'jour': entry.jour,
                        'creneau': entry.creneau,
                        'entries': list(class_entries)
                    })
        
        conflicts_report['total_conflicts'] = (
            len(conflicts_report['teacher_conflicts']) +
            len(conflicts_report['room_conflicts']) +
            len(conflicts_report['class_conflicts'])
        )
        
        return conflicts_report
