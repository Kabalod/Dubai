@echo off
echo 📧 Последние OTP письма:
echo =========================
docker compose exec realty-main-web ls -la /tmp/emails/

echo.
echo 📄 Содержимое последнего письма:
echo =================================
docker compose exec realty-main-web sh -c "ls -t /tmp/emails/ | head -1 | xargs -I {} cat /tmp/emails/{}"
