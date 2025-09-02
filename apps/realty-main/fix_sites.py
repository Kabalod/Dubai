#!/usr/bin/env python
"""
Скрипт для исправления проблемы с sites framework
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty.settings')
django.setup()

from django.db import connection

def fix_sites_table():
    """Создаем таблицу sites вручную"""
    
    with connection.cursor() as cursor:
        # Создаем таблицу sites если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS django_site (
                id INTEGER PRIMARY KEY,
                domain VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(50) NOT NULL
            )
        """)
        
        # Добавляем запись для localhost
        cursor.execute("""
            INSERT OR IGNORE INTO django_site (id, domain, name) 
            VALUES (1, 'localhost:8000', 'localhost')
        """)
        
        # Проверяем что запись создана
        cursor.execute("SELECT * FROM django_site")
        sites = cursor.fetchall()
        
        print(f"✅ Sites table created/fixed. Found {len(sites)} sites:")
        for site in sites:
            print(f"   ID: {site[0]}, Domain: {site[1]}, Name: {site[2]}")
        
        connection.commit()

if __name__ == '__main__':
    try:
        fix_sites_table()
        print("\n🎉 Sites table fixed successfully!")
    except Exception as e:
        print(f"❌ Error fixing sites table: {e}")
        import traceback
        traceback.print_exc()
