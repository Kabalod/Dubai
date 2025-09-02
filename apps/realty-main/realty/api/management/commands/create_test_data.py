#!/usr/bin/env python3
"""
Management команда для создания тестовых данных пользователей и платежей
для демонстрации функционала MVP системы

Использование:
    python manage.py create_test_data
    python manage.py create_test_data --clean  # очистить перед созданием
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
from realty.api.models import Payment, PaymentEventAudit, UserReportHistory

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые данные для демонстрации MVP: пользователи, платежи, отчеты'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Очистить существующие тестовые данные перед созданием новых'
        )
        parser.add_argument(
            '--users-count',
            type=int,
            default=5,
            help='Количество тестовых пользователей для создания (по умолчанию: 5)'
        )

    def handle(self, *args, **options):
        clean_data = options['clean']
        users_count = options['users_count']

        self.stdout.write(self.style.SUCCESS('🚀 Создание тестовых данных для MVP...'))

        if clean_data:
            self.clean_test_data()

        # Создаем тестовых пользователей
        users = self.create_test_users(users_count)
        
        # Создаем тестовые платежи
        self.create_test_payments(users)
        
        # Создаем историю отчетов
        self.create_test_reports(users)

        self.stdout.write(self.style.SUCCESS('✅ Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('🔗 Для тестирования:'))
        self.stdout.write(self.style.SUCCESS('  👤 Пользователи: /api/admin/users/'))
        self.stdout.write(self.style.SUCCESS('  💰 Платежи: /api/admin/payments/'))
        self.stdout.write(self.style.SUCCESS('  🔐 Admin панель: /admin/'))

    def clean_test_data(self):
        """Очищает тестовые данные"""
        self.stdout.write(self.style.WARNING('🧹 Очистка существующих тестовых данных...'))
        
        # Удаляем тестовых пользователей (не admin)
        test_users = User.objects.filter(
            email__contains='test',
            is_superuser=False
        )
        
        UserReportHistory.objects.filter(user__in=test_users).delete()
        PaymentEventAudit.objects.filter(related_payment__user__in=test_users).delete()
        Payment.objects.filter(user__in=test_users).delete()
        test_users.delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Очистка завершена'))

    def create_test_users(self, count):
        """Создает тестовых пользователей"""
        self.stdout.write(self.style.SUCCESS(f'👥 Создание {count} тестовых пользователей...'))
        
        users = []
        profiles = [
            {
                'username': 'investor_pro',
                'email': 'investor@testdubai.com',
                'first_name': 'Ahmed',
                'last_name': 'Al-Mansouri',
                'is_active': True
            },
            {
                'username': 'property_agent',
                'email': 'agent@testdubai.com', 
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'is_active': True
            },
            {
                'username': 'developer_dubai',
                'email': 'developer@testdubai.com',
                'first_name': 'Mohammed',
                'last_name': 'Hassan',
                'is_active': True
            },
            {
                'username': 'analyst_real_estate',
                'email': 'analyst@testdubai.com',
                'first_name': 'Elena',
                'last_name': 'Petrov',
                'is_active': True
            },
            {
                'username': 'premium_user',
                'email': 'premium@testdubai.com',
                'first_name': 'James',
                'last_name': 'Smith',
                'is_active': True
            }
        ]

        for i in range(min(count, len(profiles))):
            profile = profiles[i]
            
            user, created = User.objects.get_or_create(
                username=profile['username'],
                defaults={
                    'email': profile['email'],
                    'first_name': profile['first_name'],
                    'last_name': profile['last_name'],
                    'is_active': profile['is_active'],
                }
            )
            
            if created:
                user.set_password('testpass123')  # Тестовый пароль
                user.save()
                
            users.append(user)
            
            status = "создан" if created else "уже существует"
            self.stdout.write(
                f'  👤 {user.username} ({user.email}) - {status}'
            )

        return users

    def create_test_payments(self, users):
        """Создает тестовые платежи"""
        self.stdout.write(self.style.SUCCESS('💰 Создание тестовых платежей...'))
        
        payment_templates = [
            {
                'amount': Decimal('299.00'),
                'currency': 'AED', 
                'status': 'succeeded',
                'description': 'Premium Analytics Plan - Monthly'
            },
            {
                'amount': Decimal('999.00'),
                'currency': 'AED',
                'status': 'succeeded', 
                'description': 'Professional Report Package'
            },
            {
                'amount': Decimal('149.00'),
                'currency': 'AED',
                'status': 'succeeded',
                'description': 'Market Analysis Report'
            },
            {
                'amount': Decimal('499.00'),
                'currency': 'AED',
                'status': 'pending',
                'description': 'Investment Advisory Service'
            },
            {
                'amount': Decimal('1999.00'),
                'currency': 'AED',
                'status': 'succeeded',
                'description': 'Annual Premium Subscription'
            }
        ]

        created_payments = []
        
        for i, user in enumerate(users):
            # Создаем несколько платежей для каждого пользователя
            payment_count = random.randint(1, 3)
            
            for j in range(payment_count):
                template = payment_templates[min(i + j, len(payment_templates) - 1)]
                
                # Генерируем уникальный Stripe ID
                stripe_id = f"ch_test_{user.username}_{random.randint(100000, 999999)}"
                
                # Случайная дата в последние 30 дней
                days_ago = random.randint(0, 30)
                created_date = timezone.now() - timedelta(days=days_ago)
                
                payment = Payment.objects.create(
                    user=user,
                    stripe_charge_id=stripe_id,
                    amount=template['amount'],
                    currency=template['currency'],
                    status=template['status'],
                    description=template['description'],
                    created_at=created_date,
                    updated_at=created_date
                )
                
                created_payments.append(payment)
                
                # Создаем audit событие для каждого платежа
                PaymentEventAudit.objects.create(
                    provider='stripe',
                    event_type='charge.succeeded' if payment.status == 'succeeded' else 'charge.pending',
                    event_id=f"evt_{random.randint(100000, 999999)}_{stripe_id}",
                    payload={
                        'id': stripe_id,
                        'amount': float(payment.amount),
                        'currency': payment.currency,
                        'status': payment.status,
                        'description': payment.description
                    },
                    status='processed' if payment.status == 'succeeded' else 'received',
                    related_payment=payment,
                    created_at=created_date
                )
                
                self.stdout.write(
                    f'  💳 {payment.stripe_charge_id}: {payment.amount} {payment.currency} ({payment.status}) - {user.username}'
                )

        return created_payments

    def create_test_reports(self, users):
        """Создает историю генерации отчетов"""
        self.stdout.write(self.style.SUCCESS('📊 Создание истории отчетов...'))
        
        report_types = [
            'property_analysis',
            'market_trends', 
            'investment_report',
            'area_comparison',
            'rental_analysis'
        ]
        
        for user in users:
            # Создаем несколько отчетов для каждого пользователя
            reports_count = random.randint(2, 5)
            
            for _ in range(reports_count):
                days_ago = random.randint(1, 60)
                generated_date = timezone.now() - timedelta(days=days_ago)
                
                report_type = random.choice(report_types)
                
                report = UserReportHistory.objects.create(
                    user=user,
                    report_type=report_type,
                    generated_at=generated_date,
                    file_path=f'/reports/{user.username}/{report_type}_{generated_date.strftime("%Y%m%d")}.pdf',
                    parameters={
                        'area': random.choice(['Dubai Marina', 'Downtown Dubai', 'Jumeirah Beach Residence']),
                        'property_type': random.choice(['Apartment', 'Villa', 'Townhouse']),
                        'date_range': '2024-01-01 to 2024-12-31'
                    }
                )
                
                self.stdout.write(
                    f'  📋 {report.report_type} - {user.username} ({generated_date.strftime("%Y-%m-%d")})'
                )

    def get_test_users_summary(self):
        """Возвращает сводку по тестовым пользователям"""
        test_users = User.objects.filter(email__contains='test')
        
        summary = []
        for user in test_users:
            payments_count = Payment.objects.filter(user=user).count()
            reports_count = UserReportHistory.objects.filter(user=user).count()
            total_paid = Payment.objects.filter(
                user=user, 
                status='succeeded'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            summary.append({
                'username': user.username,
                'email': user.email,
                'payments_count': payments_count,
                'reports_count': reports_count,
                'total_paid': total_paid
            })
        
        return summary
