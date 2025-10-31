# Скрипты и лайфхаки

Полезные скрипты и лайфхаки для автоматизации повседневных задач.

## SSH Auto Connect

### Описание

`ssh_auto_connect.py` - Python-скрипт для поддержания постоянного SSH-соединения с автоматическим переподключением при разрыве связи.

### Возможности

- Автоматическое переподключение при разрыве соединения
- Настраиваемая задержка между попытками переподключения
- Логирование всех событий с временными метками
- Корректное завершение по CTRL+C
- Поддержка HPN-SSH для улучшенной производительности

### Использование

1. **Установка зависимостей:**
   ```bash
   sudo apt update
   sudo apt install openssh-client hpn-ssh
   ```

2. **Настройка скрипта:** Отредактируйте параметры подключения в начале файла:
   ```python
   SSH_HOST = "your.server.ip"  # IP адрес сервера
   SSH_USER = "username"        # Имя пользователя
   SSH_KEY = "path/to/your/key" # Путь к SSH ключу
   ```

3. **Запуск:**
   ```bash
   # Сделать исполняемым
   chmod +x ssh_auto_connect.py
   
   # Запустить
   python3 ssh_auto_connect.py
   # или
   ./ssh_auto_connect.py
   ```

## SSH Bidirectional Tunnel Manager

### Описание

`ssh_bidirectional_tunnel.py` - Продвинутый менеджер SSH туннелей с поддержкой двунаправленного проброса портов, автоматического переподключения и мониторинга состояния туннелей.

### Возможности

- **Локальные туннели (-L):** Доступ к сервисам на удаленном сервере через локальные порты
- **Удаленные туннели (-R):** Доступ к локальным сервисам с удаленного сервера
- **Автоматическое переподключение** при разрыве соединения
- **Мониторинг состояния** всех туннелей в реальном времени
- **Детальное логирование** с временными метками
- **Поддержка WSL2** и различных SSH клиентов
- **Graceful shutdown** по CTRL+C

### Использование

1. **Быстрый старт:**
   ```bash
   # Скачать скрипт
   curl -O https://raw.githubusercontent.com/KomarovAI/scripts-lifehacks/main/ssh_bidirectional_tunnel.py
   
   # Настроить параметры подключения
   nano ssh_bidirectional_tunnel.py
   
   # Запустить
   python3 ssh_bidirectional_tunnel.py start
   ```

2. **Настройка сервера (VPS):**
   ```bash
   # Автоматическая настройка SSH для туннелирования
   curl -s https://raw.githubusercontent.com/KomarovAI/scripts-lifehacks/main/setup_vps_ssh.sh | bash
   ```

### Конфигурация

Отредактируйте переменные в начале скрипта:

```python
# Основные параметры подключения
SSH_HOST = "31.59.58.96"
SSH_USER = "root" 
SSH_KEY = "/home/user/.ssh/openssh_imported.key"

# Локальные форварды (ПК <- ВПС)
LOCAL_FORWARDS = [
    "8080:localhost:80",     # Веб-сервер
    "8443:localhost:443",    # HTTPS
    "3306:localhost:3306",   # MySQL
]

# Удаленные форварды (ВПС <- ПК)  
REMOTE_FORWARDS = [
    # Пример: "2223:localhost:22",
]
```

### Примеры использования

**Доступ к веб-сервисам ВПС:**
```bash
# После запуска туннелей доступно:
curl http://localhost:8080        # Веб-сервер с ВПС
curl https://localhost:8443       # HTTPS с ВПС
mysql -h localhost -P 3306        # MySQL с ВПС
```

**Удаленный доступ к ПК через ВПС:**
```bash
# На ВПС подключиться к вашему ПК (если включили -R):
ssh -p 2223 localhost
```

### Диагностика проблем

1. **Полная диагностика сети (WSL):**
   ```bash
   curl -s https://raw.githubusercontent.com/KomarovAI/scripts-lifehacks/bidirectional-ssh-improvements/network_ssh_diagnostics.sh | bash
   ```

2. **Диагностика VPS:**
   ```bash
   curl -s https://raw.githubusercontent.com/KomarovAI/scripts-lifehacks/bidirectional-ssh-improvements/vps_diagnostics.sh | bash
   ```

### Возможные проблемы и решения

1. **WSL2 сообщает filtered/висит:**
   - Отключите Windows Firewall: `Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False`
   - Либо добавьте outbound-правило на порт 2222

2. **Порт заблокирован на VPS:**
   ```bash
   sudo ufw allow 2222/tcp  # Разрешить SSH порт
   sudo ufw status          # Проверить статус
   ```

3. **SSH ключ недоступен:**
   ```bash
   chmod 600 ~/.ssh/your_key
   ```

4. **Соединение разрывается (код 255):**
   - Проверьте AllowTcpForwarding=yes и GatewayPorts=yes на VPS
   - Упростите список форвардов и добавляйте по одному

## Утилиты диагностики

- `network_ssh_diagnostics.sh` — диагностика сети/SSH в WSL
- `vps_diagnostics.sh` — диагностика VPS
- `setup_vps_ssh.sh` — автонастройка sshd для туннелей

## Системные требования

- ОС: Linux, WSL2, macOS
- Python 3.6+
- SSH клиент: OpenSSH или HPN-SSH

## Лицензия

MIT License - свободное использование и модификация.

## Вклад в проект

Пул-реквесты приветствуются! Для серьёзных изменений сначала откройте issue для обсуждения.
