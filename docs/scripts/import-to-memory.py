#!/usr/bin/env python3
"""
Скрипт для импорта всей документации Dubai Platform в Memory LLM сервис
"""

import os
import json
import requests
from pathlib import Path
import markdown
from bs4 import BeautifulSoup
import re

class DocumentationImporter:
    def __init__(self, memory_llm_url="http://localhost:8080"):
        self.memory_llm_url = memory_llm_url
        self.docs_path = Path(__file__).parent.parent
        self.imported_count = 0
        self.errors = []

    def extract_text_from_markdown(self, file_path):
        """Извлекает чистый текст из Markdown файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Конвертируем Markdown в HTML
            html = markdown.markdown(content, extensions=['toc', 'tables', 'fenced_code'])
            
            # Извлекаем чистый текст
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Очищаем текст
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            return text.strip()
        except Exception as e:
            self.errors.append(f"Ошибка при обработке {file_path}: {e}")
            return None

    def get_file_metadata(self, file_path):
        """Получает метаданные файла"""
        rel_path = file_path.relative_to(self.docs_path)
        
        # Определяем категорию по пути
        if 'api' in str(rel_path):
            category = 'api'
        elif 'architecture' in str(rel_path):
            category = 'architecture'
        elif 'deployment' in str(rel_path):
            category = 'deployment'
        elif 'development' in str(rel_path):
            category = 'development'
        elif 'user-guides' in str(rel_path):
            category = 'user_guides'
        elif 'troubleshooting' in str(rel_path):
            category = 'troubleshooting'
        else:
            category = 'general'

        return {
            "file_path": str(rel_path),
            "category": category,
            "file_type": "documentation",
            "platform": "dubai",
            "language": "ru",
            "version": "1.0.0"
        }

    def import_file_to_memory(self, file_path):
        """Импортирует файл в Memory LLM"""
        try:
            # Извлекаем текст
            content = self.extract_text_from_markdown(file_path)
            if not content:
                return False

            # Получаем метаданные
            metadata = self.get_file_metadata(file_path)
            
            # Подготавливаем данные для импорта
            import_data = {
                "content": content,
                "metadata": metadata
            }

            # Отправляем в Memory LLM
            response = requests.post(
                f"{self.memory_llm_url}/api/v1/vectors/add",
                json=import_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                self.imported_count += 1
                print(f"✅ Импортирован: {file_path.name}")
                return True
            else:
                error_msg = f"Ошибка HTTP {response.status_code}: {response.text}"
                self.errors.append(f"Ошибка при импорте {file_path.name}: {error_msg}")
                print(f"❌ Ошибка: {file_path.name} - {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка соединения: {e}"
            self.errors.append(f"Ошибка соединения для {file_path.name}: {error_msg}")
            print(f"❌ Ошибка соединения: {file_path.name}")
            return False
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {e}"
            self.errors.append(f"Неожиданная ошибка для {file_path.name}: {error_msg}")
            print(f"❌ Неожиданная ошибка: {file_path.name}")
            return False

    def find_markdown_files(self):
        """Находит все Markdown файлы в документации"""
        markdown_files = []
        
        for file_path in self.docs_path.rglob("*.md"):
            if file_path.name not in ['README.md', 'index.md']:  # Пропускаем главные файлы
                markdown_files.append(file_path)
        
        return sorted(markdown_files)

    def import_all_documentation(self):
        """Импортирует всю документацию"""
        print("🚀 Начинаем импорт документации в Memory LLM...")
        print(f"📁 Путь к документации: {self.docs_path}")
        
        # Находим все Markdown файлы
        markdown_files = self.find_markdown_files()
        print(f"📚 Найдено файлов для импорта: {len(markdown_files)}")
        
        # Импортируем каждый файл
        for file_path in markdown_files:
            self.import_file_to_memory(file_path)
        
        # Выводим результаты
        self.print_summary()

    def print_summary(self):
        """Выводит сводку импорта"""
        print("\n" + "="*50)
        print("📊 СВОДКА ИМПОРТА ДОКУМЕНТАЦИИ")
        print("="*50)
        print(f"✅ Успешно импортировано: {self.imported_count}")
        print(f"❌ Ошибок: {len(self.errors)}")
        
        if self.errors:
            print("\n🔍 ДЕТАЛИ ОШИБОК:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("\n🎯 Документация готова для использования в Memory LLM!")
        print("🔍 Теперь можно искать информацию через векторный поиск")

    def test_connection(self):
        """Тестирует соединение с Memory LLM"""
        try:
            response = requests.get(f"{self.memory_llm_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Соединение с Memory LLM установлено: {self.memory_llm_url}")
                return True
            else:
                print(f"❌ Memory LLM недоступен: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Не удается подключиться к Memory LLM: {e}")
            return False

def main():
    """Главная функция"""
    print("🌟 Dubai Platform - Импорт документации в Memory LLM")
    print("="*60)
    
    # Создаем импортер
    importer = DocumentationImporter()
    
    # Тестируем соединение
    if not importer.test_connection():
        print("\n💡 Убедитесь, что Memory LLM сервис запущен:")
        print("   docker compose -f docker-compose.monitoring.yml up -d")
        print("\n💡 Или измените URL в скрипте")
        return
    
    # Импортируем документацию
    importer.import_all_documentation()

if __name__ == "__main__":
    main()
