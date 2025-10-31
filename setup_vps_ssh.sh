#!/bin/bash
# Автоматическая настройка SSH на ВПС для туннелирования
# Использование: curl -s https://raw.githubusercontent.com/KomarovAI/scripts-lifehacks/bidirectional-ssh-improvements/setup_vps_ssh.sh | bash

echo "=== Настройка SSH для туннелирования ==="

# Создаем backup
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backup создан: /etc/ssh/sshd_config.backup.*"

# Применяем настройки
sed -i 's/#AllowTcpForwarding yes/AllowTcpForwarding yes/' /etc/ssh/sshd_config
sed -i 's/#AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config
sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config

sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config
sed -i 's/#GatewayPorts yes/GatewayPorts yes/' /etc/ssh/sshd_config
sed -i 's/GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config

sed -i 's/#ClientAliveInterval 0/ClientAliveInterval 30/' /etc/ssh/sshd_config
sed -i 's/#ClientAliveInterval [0-9]*/ClientAliveInterval 30/' /etc/ssh/sshd_config
sed -i 's/ClientAliveInterval 0/ClientAliveInterval 30/' /etc/ssh/sshd_config

sed -i 's/#ClientAliveCountMax 3/ClientAliveCountMax 3/' /etc/ssh/sshd_config
sed -i 's/#ClientAliveCountMax [0-9]*/ClientAliveCountMax 3/' /etc/ssh/sshd_config

# Добавляем строки если их нет
grep -q "^AllowTcpForwarding" /etc/ssh/sshd_config || echo "AllowTcpForwarding yes" >> /etc/ssh/sshd_config
grep -q "^GatewayPorts" /etc/ssh/sshd_config || echo "GatewayPorts yes" >> /etc/ssh/sshd_config
grep -q "^ClientAliveInterval" /etc/ssh/sshd_config || echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config
grep -q "^ClientAliveCountMax" /etc/ssh/sshd_config || echo "ClientAliveCountMax 3" >> /etc/ssh/sshd_config

echo "✓ Настройки применены"

# Проверяем синтаксис
if sshd -t; then
    echo "✓ Синтаксис конфига корректен"
    
    # Перезагружаем SSH
    systemctl reload sshd
    echo "✓ SSH перезагружен"
    
    # Показываем текущие настройки
    echo ""
    echo "=== Текущие настройки ==="
    grep -E "^(AllowTcpForwarding|GatewayPorts|ClientAliveInterval|ClientAliveCountMax)" /etc/ssh/sshd_config
    
    echo ""
    echo "✅ Настройка завершена! Теперь можно запускать туннели с ПК"
else
    echo "❌ Ошибка в конфигурации SSH!"
    echo "Восстанавливаем из backup..."
    cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
    systemctl reload sshd
    echo "Backup восстановлен"
    exit 1
fi