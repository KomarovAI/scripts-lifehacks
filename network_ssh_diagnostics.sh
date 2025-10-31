#!/bin/bash
# Полная диагностика сети и SSH соединения
# Для WSL и VPS

TARGET_HOST="31.59.58.96"
SSH_PORT="2222"
SSH_KEY="$HOME/.ssh/openssh_imported.key"

echo "=== ПОЛНАЯ ДИАГНОСТИКА СЕТИ И SSH ==="
echo "Цель: $TARGET_HOST:$SSH_PORT"
echo "Дата: $(date)"
echo ""

echo "=== 1. ИНФОРМАЦИЯ О СИСТЕМЕ ==="
echo "OS: $(uname -a)"
echo "WSL версия: $(cat /proc/version 2>/dev/null | grep -i microsoft || echo 'Не WSL')"
echo "IP адреса:"
ip addr show | grep -E "inet.*scope global"
echo ""

echo "=== 2. СЕТЕВЫЕ МАРШРУТЫ ==="
echo "Маршруты:"
ip route
echo ""
echo "DNS серверы:"
cat /etc/resolv.conf
echo ""

echo "=== 3. PING ТЕСТ ==="
echo "Ping $TARGET_HOST:"
ping -c 3 $TARGET_HOST
echo ""

echo "=== 4. ТРАССИРОВКА ==="
echo "Traceroute к $TARGET_HOST:"
traceroute -m 10 $TARGET_HOST 2>/dev/null || echo "traceroute не установлен"
echo ""

echo "=== 5. ПРОВЕРКА ПОРТОВ (nmap) ==="
if command -v nmap >/dev/null 2>&1; then
    echo "Сканирование портов $TARGET_HOST:"
    nmap -p 22,2222,80,443,3306 $TARGET_HOST
else
    echo "nmap не установлен, устанавливаем..."
    sudo apt update && sudo apt install -y nmap
    nmap -p 22,2222,80,443,3306 $TARGET_HOST
fi
echo ""

echo "=== 6. ТЕСТ TCP СОЕДИНЕНИЯ ==="
echo "Проверка порта $SSH_PORT через nc:"
timeout 10 nc -zv $TARGET_HOST $SSH_PORT 2>&1
echo ""

echo "Проверка порта 22 через nc:"
timeout 10 nc -zv $TARGET_HOST 22 2>&1
echo ""

echo "=== 7. ТЕСТ ЧЕРЕЗ socat ==="
if command -v socat >/dev/null 2>&1; then
    echo "Тест соединения socat:"
    timeout 5 socat - TCP:$TARGET_HOST:$SSH_PORT,connect-timeout=5 </dev/null 2>&1
else
    echo "socat не установлен, устанавливаем..."
    sudo apt install -y socat
    timeout 5 socat - TCP:$TARGET_HOST:$SSH_PORT,connect-timeout=5 </dev/null 2>&1
fi
echo ""

echo "=== 8. SSH КЛЮЧИ И НАСТРОЙКИ ==="
echo "SSH ключ существует:"
ls -la $SSH_KEY 2>/dev/null || echo "SSH ключ не найден: $SSH_KEY"
echo ""

echo "Права на SSH ключ:"
stat $SSH_KEY 2>/dev/null || echo "Не удается получить информацию о ключе"
echo ""

echo "SSH known_hosts:"
ls -la ~/.ssh/known_hosts* 2>/dev/null || echo "known_hosts не найден"
echo ""

echo "=== 9. ТЕСТ SSH ПОДКЛЮЧЕНИЯ (verbose) ==="
echo "SSH подключение с отладкой (10 сек):"
timeout 10 ssh -vvv -p $SSH_PORT -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$TARGET_HOST echo "SSH OK" 2>&1
echo ""

echo "=== 10. ЛОКАЛЬНЫЕ СЕТЕВЫЕ ПРОЦЕССЫ ==="
echo "Локальные слушающие порты:"
ss -tlnp | head -20
echo ""

echo "=== 11. FIREWALL STATUS ==="
echo "iptables правила:"
sudo iptables -L 2>/dev/null || echo "iptables недоступен"
echo ""

echo "ufw статус:"
sudo ufw status 2>/dev/null || echo "ufw не установлен"
echo ""

echo "=== 12. WSL СПЕЦИФИЧНЫЕ ТЕСТЫ ==="
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "WSL обнаружен, дополнительные проверки:"
    echo "Windows хост из resolv.conf:"
    grep nameserver /etc/resolv.conf
    echo ""
    
    echo "Интерфейсы WSL:"
    ip link show
    echo ""
    
    echo "WSL сетевые настройки:"
    cat /etc/wsl.conf 2>/dev/null || echo "/etc/wsl.conf не найден"
    echo ""
fi

echo "=== ДИАГНОСТИКА ЗАВЕРШЕНА ==="
echo "Сохранить результат в файл? (y/n)"
read -t 5 save_result
if [ "$save_result" = "y" ]; then
    echo "Результат сохранен в network_diagnostic.log"
    bash $0 > network_diagnostic.log 2>&1
fi