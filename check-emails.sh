#!/bin/bash
# Скрипт для просмотра OTP писем

echo "📧 Последние OTP письма:"
echo "========================="

# Показываем все письма
docker compose exec realty-main-web ls -la /tmp/emails/ | grep -v "^total"

echo ""
echo "📄 Содержимое последнего письма:"
echo "================================="

# Читаем последнее письмо
LATEST_FILE=$(docker compose exec realty-main-web ls -t /tmp/emails/ | head -1)
if [ ! -z "$LATEST_FILE" ]; then
    docker compose exec realty-main-web cat "/tmp/emails/$LATEST_FILE"
else
    echo "Писем пока нет. Попробуйте отправить OTP."
fi
