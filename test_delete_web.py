#!/usr/bin/env python
"""
Test de suppression via une requête web simulée
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_delete_attribution():
    """
    Teste la suppression d'une attribution via l'API web
    """
    print("=" * 60)
    print("TEST DE SUPPRESSION VIA L'API WEB")
    print("=" * 60)
    
    # Trouver une attribution à supprimer (ID à adapter)
    attribution_id = input("\nEntrez l'ID de l'attribution à supprimer (ou appuyez sur Entrée pour annuler): ")
    
    if not attribution_id:
        print("Test annulé.")
        return
    
    try:
        attribution_id = int(attribution_id)
    except ValueError:
        print("❌ ID invalide")
        return
    
    # Confirmer
    confirm = input(f"\n⚠️  Êtes-vous sûr de vouloir supprimer l'attribution ID={attribution_id}? (oui/non): ")
    if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Test annulé.")
        return
    
    # Tenter la suppression
    print(f"\n🔄 Tentative de suppression de l'attribution ID={attribution_id}...")
    
    url = f"{BASE_URL}/attribution/delete-attribution/{attribution_id}/"
    
    try:
        response = requests.post(url)
        
        print(f"\nCode de statut: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ SUCCÈS: {data.get('message')}")
                print("\n🎉 La suppression fonctionne correctement!")
            else:
                print(f"❌ ÉCHEC: {data.get('error')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"Réponse: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Django")
        print("   Assurez-vous que le serveur tourne sur http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_delete_web()
