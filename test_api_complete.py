#!/usr/bin/env python3
"""
Script de test complet de l'API INF349
Teste tous les endpoints et scénarios
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:5000"

def test_api():
    """Test complet de l'API"""
    print(" Test Complet de l'API INF349")
    print("=" * 50)
    
    try:
        # Test 1: Vérifier que le serveur est en ligne
        print(" Test: Vérification serveur...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        print(" Serveur en ligne")
        
        # Test 2: Obtenir les produits
        print("\n Test: GET /products")
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        products = response.json()['products']
        assert len(products) > 0
        print(f" {len(products)} produits récupérés")
        
        # Test 3: Créer une commande valide
        print("\n Test: POST /order (commande valide)")
        order_data = {
            "product": {
                "id": 1,
                "quantity": 2
            }
        }
        
        response = requests.post(f"{BASE_URL}/order", 
                               json=order_data)
        assert response.status_code == 302
        location = response.headers.get('Location')
        assert location is not None
        order_id = int(location.split('/')[-1])
        print(f" Commande {order_id} créée")
        
        # Test 4: Consulter la commande
        print("\n Test: GET /order/<id>")
        response = requests.get(f"{BASE_URL}/order/{order_id}")
        assert response.status_code == 200
        order = response.json()['order']
        assert order['id'] == order_id
        assert order['product']['id'] == 1
        assert order['product']['quantity'] == 2
        assert order['paid'] == False
        print(f" Commande {order_id} consultée")
        print(f"   - Prix total: {order['total_price']} cents")
        print(f"   - Prix expédition: {order['shipping_price']} cents")
        print(f"   - Prix avec taxe: {order['total_price_tax']}")
        
        # Test 5: Mettre à jour les informations client
        print("\n5️⃣ Test: PUT /order/<id> (infos client)")
        update_data = {
            "order": {
                "email": "test@example.com",
                "shipping_information": {
                    "country": "Canada",
                    "address": "123 Test St",
                    "postal_code": "G7X 3Y7",
                    "city": "Chicoutimi",
                    "province": "QC"
                }
            }
        }
        
        response = requests.put(f"{BASE_URL}/order/{order_id}",
                              json=update_data)
        assert response.status_code == 200
        order = response.json()['order']
        assert order['email'] == "test@example.com"
        assert order['shipping_information']['province'] == "QC"
        print(f" Infos client mises à jour")
        print(f"   - Email: {order['email']}")
        print(f"   - Province: {order['shipping_information']['province']}")
        
        # Test 6: Créer une commande avec produit hors stock
        print("\n Test: POST /order (produit hors stock)")
        # Trouver un produit hors stock
        out_of_stock = None
        for product in products:
            if not product['in_stock']:
                out_of_stock = product
                break
        
        if out_of_stock:
            invalid_order = {
                "product": {
                    "id": out_of_stock['id'],
                    "quantity": 1
                }
            }
            
            response = requests.post(f"{BASE_URL}/order", json=invalid_order)
            assert response.status_code == 422
            errors = response.json()['errors']
            assert errors['product']['code'] == 'out-of-inventory'
            print(f" Produit hors stock rejeté (ID: {out_of_stock['id']})")
        else:
            print("  Aucun produit hors stock trouvé pour le test")
        
        # Test 7: Créer une commande avec champs manquants
        print("\n Test: POST /order (champs manquants)")
        invalid_order = {
            "product": {
                "id": 1
                # quantity manquant
            }
        }
        
        response = requests.post(f"{BASE_URL}/order", json=invalid_order)
        assert response.status_code == 422
        errors = response.json()['errors']
        assert errors['product']['code'] == 'missing-fields'
        print(" Champs manquants détectés")
        
        # Test 8: Consulter une commande inexistante
        print("\n Test: GET /order/999 (inexistant)")
        response = requests.get(f"{BASE_URL}/order/999")
        assert response.status_code == 404
        print(" Commande inexistante détectée")
        
        # Test 9: Paiement sans infos client
        print("\n Test: PUT /order/<id> (paiement sans infos client)")
        payment_data = {
            "credit_card": {
                "name": "John Doe",
                "number": "4242 4242 4242 4242",
                "expiration_year": 2024,
                "expiration_month": 9,
                "cvv": "123"
            }
        }
        
        # Créer une nouvelle commande pour ce test
        response = requests.post(f"{BASE_URL}/order", json=order_data)
        order_id_2 = int(response.headers['Location'].split('/')[-1])
        
        response = requests.put(f"{BASE_URL}/order/{order_id_2}", json=payment_data)
        assert response.status_code == 422
        errors = response.json()['errors']
        assert errors['order']['code'] == 'missing-fields'
        print(" Paiement sans infos client rejeté")
        
        print("\n" + "=" * 50)
        print("TOUS LES TESTS RÉUSSIS!")
        print(" API 100% fonctionnelle")
        return True
        
    except requests.exceptions.ConnectionError:
        print(" ERREUR: Serveur non démarré")
        print(" Démarrez l'application avec: python start_app.py")
        return False
    except AssertionError as e:
        print(f" ERREUR: Test échoué - {e}")
        return False
    except Exception as e:
        print(f" ERREUR: {e}")
        return False

def main():
    """Fonction principale"""
    print(" Test de l'API INF349")
    print("Assurez-vous que l'application est démarrée:")
    print("   python start_app.py")
    print()
    
    # Attendre que l'utilisateur soit prêt
    input("Appuyez sur Entrée pour commencer les tests...")
    
    success = test_api()
    
    if success:
        print("\n L'application est prête pour la démonstration!")
        return 0
    else:
        print("\n Corrigez les erreurs avant de continuer.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
