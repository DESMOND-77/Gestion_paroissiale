#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_p.settings')
django.setup()

import redis
from django.conf import settings
from django.core.cache import cache

def test_redis_connection():
    """Test la connexion Redis."""
    print("🧪 Test de connexion Redis...")
    
    try:
        # Test via django-redis
        cache.set('test_key', 'redis_is_working', 10)
        result = cache.get('test_key')
        
        if result == 'redis_is_working':
            print("✅ Cache Django avec Redis fonctionne!")
        else:
            print("❌ Problème avec django-redis")
            return False
        
        # Test direct Redis
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        print("✅ Connexion Redis directe fonctionne!")
        
        # Test des performances
        import time
        start = time.time()
        for i in range(100):
            cache.set(f'perf_test_{i}', f'value_{i}', 30)
        elapsed = time.time() - start
        print(f"✅ Performance: 100 écritures en {elapsed:.2f}s ({elapsed*10:.1f}ms/op)")
        
        # Nettoyage
        for i in range(100):
            cache.delete(f'perf_test_{i}')
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")
        return False

def test_token_storage():
    """Test le stockage des tokens."""
    print("\n🧪 Test du stockage des tokens...")
    
    from accounts.models import User 
    from core.jwt_utils import TokenManager
    
    try:
        # Créer un utilisateur de test
        etab = Etablissement.objects.get_or_create(id="epm70")
        
            
        user, created = User.objects.get_or_create(
            username='test_user_redis',
            etablissement=etab[0],
            defaults={'email': 'test@redis.com', 'password': 'test123'}
        )
        # Générer un token
        token_data = TokenManager.generate_token(user)
        
        if token_data:
            print(f"✅ Token généré avec succès")
            print(f"   Access token: {token_data['access'][:50]}...")
            print(f"   Durée: {token_data['access_expires_in']} secondes")
            
            # Vérifier le stockage Redis
            jti = token_data.get('refresh', '').split('.')[0] if '.' in token_data.get('refresh', '') else 'unknown'
            if TokenManager._store_token_metadata(
                user.id, 
                jti, 
                'refresh', 
                token_data['refresh_expires_in']
            ):
                print("✅ Métadata du token stockée dans Redis")
            else:
                print("❌ Échec du stockage des métadata")
            
            return True
        else:
            print("❌ Échec de génération du token")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des tokens: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Test de configuration Redis")
    print("=" * 50)
    
    conn_ok = test_redis_connection()
    token_ok = test_token_storage()
    
    print("\n" + "=" * 50)
    if conn_ok and token_ok:
        print("✅ Tous les tests Redis sont réussis!")
    else:
        print("❌ Certains tests ont échoué")
    print("=" * 50)