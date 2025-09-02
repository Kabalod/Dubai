# Новые чистые миграции для Dubai MVP
# Создано: 2025-08-26 - Полная очистка от старых проблем

from django.conf import settings
from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='api_user_set', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='api_user_set', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='OTPCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('attempts', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'OTP Code',
                'verbose_name_plural': 'OTP Codes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_charge_id', models.CharField(default='', max_length=100, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('currency', models.CharField(default='AED', max_length=10)),
                ('status', models.CharField(default='succeeded', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentEventAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=32)),
                ('event_type', models.CharField(max_length=64)),
                ('event_id', models.CharField(max_length=128, unique=True)),
                ('payload', models.JSONField(default=dict)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(default='received', max_length=32)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('related_payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='webhook_events', to='api.payment')),
            ],
            options={
                'verbose_name': 'Payment Event Audit',
                'verbose_name_plural': 'Payment Event Audits',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserReportHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(default='property_analysis', max_length=50)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('file_path', models.CharField(blank=True, max_length=500)),
                ('parameters', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Report History',
                'verbose_name_plural': 'User Report Histories',
                'ordering': ['-generated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='otpcode',
            index=models.Index(fields=['email'], name='api_otpcode_email_bee0a2_idx'),
        ),
        migrations.AddIndex(
            model_name='otpcode',
            index=models.Index(fields=['created_at'], name='api_otpcode_created_572054_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user'], name='api_payment_user_id_03c2cf_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['stripe_charge_id'], name='api_payment_stripe__0cead4_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status'], name='api_payment_status_c61efc_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenteventaudit',
            index=models.Index(fields=['provider', 'event_id'], name='api_payment_provide_59f71e_idx'),
        ),
        migrations.AddIndex(
            model_name='paymenteventaudit',
            index=models.Index(fields=['event_type'], name='api_payment_event_t_1402b4_idx'),
        ),
        migrations.AddIndex(
            model_name='userreporthistory',
            index=models.Index(fields=['user'], name='api_userrepor_user_id_0a1234_idx'),
        ),
        migrations.AddIndex(
            model_name='userreporthistory',
            index=models.Index(fields=['report_type'], name='api_userrepor_report__5b2345_idx'),
        ),
        migrations.AddIndex(
            model_name='userreporthistory',
            index=models.Index(fields=['generated_at'], name='api_userrepor_generat_6c3456_idx'),
        ),
    ]

