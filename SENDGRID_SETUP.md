# 🚀 Настройка SendGrid для OTP отправки

## Шаг 1: Создание SendGrid аккаунта

1. **Регистрация**: Перейдите на https://sendgrid.com/ и зарегистрируйтесь
2. **Подтверждение email**: Подтвердите ваш email адрес
3. **Verification процесс**: SendGrid может запросить дополнительную информацию

## Шаг 2: Создание и верификация Sender Identity

⚠️ **ВАЖНО**: Без этого шага письма НЕ будут отправляться!

1. В панели SendGrid перейдите в **Settings** → **Sender Authentication**
2. Выберите **Single Sender Verification**
3. Добавьте email с которого будут отправляться письма
4. Заполните форму:
   - **From Name**: Dubai Real Estate
   - **From Email**: ваш-verified-email@domain.com
   - **Reply To**: тот же email
   - **Company Address**: любой адрес
5. Нажмите **Create** и подтвердите email

## Шаг 3: Получение API ключа

1. Перейдите в **Settings** → **API Keys**
2. Нажмите **Create API Key**
3. Выберите **Restricted Access**
4. Дайте название: "Dubai Real Estate OTP"
5. В разрешениях выберите:
   - **Mail Send**: Full Access
   - Остальное можно оставить "No Access"
6. Нажмите **Create & View**
7. **СКОПИРУЙТЕ ключ** - он больше не покажется!

## Шаг 4: Настройка проекта

Ключ будет выглядеть как: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

Сохраните его - мы добавим в настройки!
