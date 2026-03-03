#!/usr/bin/env python3
"""
Script de lancement pour l'application INF349
Ce script initialise et démarre l'application Flask
"""
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, '.')

from inf349 import create_app
from inf349.models import initialize_db
from inf349 import db

def main():
    """Initialiser et démarrer l'application"""
    print("🚀 Démarrage de l'application INF349...")
    print("=" * 50)
    
    # Créer l'application
    app = create_app()
    
    with app.app_context():
        try:
            # Initialiser la base de données
            print("📦 Initialisation de la base de données...")
            initialize_db(db)
            
            # Récupérer les produits depuis le service distant
            from inf349.services import ProductService
            product_service = ProductService(app.config['PRODUCT_SERVICE_URL'])
            products = product_service.fetch_products()
            print(f"✅ {len(products)} produits récupérés avec succès")
            
            print("\n🎯 Application prête!")
            print("📍 URL: http://localhost:5000")
            print("📚 Documentation: Voir README.md")
            print("🧪 Tests: python run_tests.py")
            print("\n" + "=" * 50)
            
            # Démarrer le serveur Flask
            app.run(host='0.0.0.0', port=5000, debug=True)
            
        except Exception as e:
            print(f"❌ Erreur lors du démarrage: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
