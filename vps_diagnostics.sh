#!/bin/bash
# Диагностика VPS для SSH туннелирования

echo "=== ДИАГНОСТИКА VPS ДЛЯ SSH ТУННЕЛИРОВАНИЯ ==="
echo "Дата: $(date)"
echo "Хост: $(hostname) ($(whoami))"
echo ""

echo "=== 1. СИСТЕМНАЯ ИНФОРМАЦИЯ ==="
echo "OS: $(uname -a)"
echo "IP адреса:"
ip addr show | grep -E "inet.*scope global"
echo ""

echo "=== 2. SSH КОНФИГУРАЦИЯ ==="
echo "SSH порты в sshd_config:"
grep -E "^Port|^#Port" /etc/ssh/sshd_config
echo ""

echo "Ключевые настройки SSH:"
grep -E "^(AllowTcpForwarding|GatewayPorts|ClientAliveInterval|ClientAliveCountMax|PasswordAuthentication|PubkeyAuthentication)" /etc/ssh/sshd_config
echo ""

echo "=== 3. СЛУШАЮЩИЕ ПОРТЫ ==="
echo "SSH порты:"
ss -tlnp | grep sshd
echo ""

echo "Все слушающие TCP порты:"
ss -tlnp | grep -E ":(22|80|443|3306|8080|9090|2222)" | sort -t: -k2 -n
echo ""

echo "=== 4. DOCKER КОНТЕЙНЕРЫ ==="
if command -v docker >/dev/null 2>&1; then
    echo "Docker контейнеры:"
    docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
    echo ""
    
    echo "Docker сети:"
    docker network ls
else
    echo "Docker не установлен"
fi
echo ""

echo "=== 5. NGINX/WEB СЕРВЕРЫ ==="
echo "Проверка localhost:80:"
curl -I http://localhost:80 2>/dev/null | head -5 || echo "Не отвечает"
echo ""

echo "Проверка localhost:443:"
curl -I -k https://localhost:443 2>/dev/null | head -5 || echo "Не отвечает"
echo ""

echo "Проверка 127.0.0.1:80:"
curl -I http://127.0.0.1:80 2>/dev/null | head -5 || echo "Не отвечает"
echo ""

echo "=== 6. БАЗЫ ДАННЫХ ==="
echo "Проверка MySQL/MariaDB на localhost:3306:"
if command -v mysql >/dev/null 2>&1; then
    timeout 5 mysql -u root -h localhost -P 3306 -e "SELECT 1;" 2>/dev/null && echo "MySQL доступен" || echo "MySQL недоступен"
else
    nc -zv localhost 3306 2>&1 | grep -E "succeeded|open" && echo "MySQL порт открыт" || echo "MySQL порт закрыт"
fi
echo ""

echo "=== 7. FIREWALL ==="
echo "iptables правила:"
iptables -L INPUT -n | head -10
echo ""

echo "ufw статус:"
ufw status 2>/dev/null || echo "ufw не установлен"
echo ""

echo "=== 8. SSH ПОДКЛЮЧЕНИЯ ==="
echo "Активные SSH сессии:"
who
echo ""

echo "SSH процессы:"
ps aux | grep sshd: | grep -v grep
echo ""

echo "=== 9. ЛОГИ SSH ==="
echo "Последние 10 строк SSH логов:"
tail -10 /var/log/auth.log 2>/dev/null || tail -10 /var/log/secure 2>/dev/null || echo "Логи SSH не найдены"
echo ""

echo "=== 10. ТЕСТ ЛОКАЛЬНЫХ СОЕДИНЕНИЙ ==="
echo "Тест SSH к localhost:22:"
nc -zv localhost 22 2>&1 | grep -E "succeeded|open|refused" || echo "Нет ответа"
echo ""

echo "Тест SSH к localhost:2222:"
nc -zv localhost 2222 2>&1 | grep -E "succeeded|open|refused" || echo "Нет ответа"
echo ""

echo "=== 11. СИСТЕМНЫЕ ПАРАМЕТРЫ ==="
echo "Нагрузка системы:"
uptime
echo ""

echo "Память:"
free -h
echo ""

echo "Дисковое пространство:"
df -h | head -5
echo ""

echo "=== ДИАГНОСТИКА VPS ЗАВЕРШЕНА ==="