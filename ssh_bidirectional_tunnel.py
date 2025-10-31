#!/usr/bin/env python3
"""
Улучшенный SSH-скрипт с двунаправленным туннелированием
Поддерживает:
- Постоянное соединение между ВПС и локальным компьютером
- Локальное и удаленное проброс портов
- Автоматическое переподключение
- Мониторинг всех сервисов
"""

import subprocess
import time
import sys
import signal
import os
import json
import threading
import socket
from typing import List, Dict, Optional

# ===== КОНФИГУРАЦИЯ =====

# Основные параметры подключения
SSH_HOST = "31.59.58.96"
SSH_USER = "root"
SSH_KEY = f"{os.path.expanduser('~')}/.ssh/openssh_imported.key"

# Параметры переподключения
RETRY_DELAY = 5
MAX_RETRIES = 0  # 0 = бесконечные попытки

# Настройки туннелей
# LOCAL_FORWARDS: локальный_порт:удаленный_хост:удаленный_порт
# Пример: 8080:localhost:80 - локальный порт 8080 перенаправляется на удаленный порт 80
LOCAL_FORWARDS = [
    "8080:localhost:80",     # Веб-сервер
    "8443:localhost:443",    # HTTPS
    "3306:localhost:3306",   # MySQL
    "5432:localhost:5432",   # PostgreSQL
    "6379:localhost:6379",   # Redis
    "9090:localhost:9090",   # Cockpit panel
    "2222:localhost:22",     # SSH доступ к ВПС
]

# REMOTE_FORWARDS: удаленный_порт:локальный_хост:локальный_порт
# Пример: 8081:localhost:80 - удаленный порт 8081 перенаправляется на локальный порт 80
REMOTE_FORWARDS = [
    "8081:localhost:80",     # Локальный веб-сервер доступен на ВПС через порт 8081
    "3307:localhost:3306",   # Локальная БД доступна на ВПС
    "2223:localhost:22",     # SSH к локальному компьютеру через ВПС
]

# Дополнительные опции SSH
SSH_OPTIONS = [
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=30", 
    "-o", "ServerAliveCountMax=3",
    "-o", "ExitOnForwardFailure=no",
    "-o", "GatewayPorts=yes",  # Позволяет подключения к удаленным портам извне
    "-o", "TCPKeepAlive=yes",
    "-N",  # Не выполнять удаленные команды, только туннели
]

class SSHTunnelManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.retry_count = 0
        
    def build_ssh_command(self) -> List[str]:
        """Строит команду SSH с туннелями"""
        cmd = ["ssh", "-i", SSH_KEY] + SSH_OPTIONS
        
        # Добавляем локальные форварды (-L)
        for forward in LOCAL_FORWARDS:
            cmd.extend(["-L", forward])
            
        # Добавляем удаленные форварды (-R)
        for forward in REMOTE_FORWARDS:
            cmd.extend(["-R", forward])
            
        cmd.append(f"{SSH_USER}@{SSH_HOST}")
        return cmd
        
    def test_port(self, host: str, port: int, timeout: float = 3) -> bool:
        """Проверяет доступность порта"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
            
    def check_tunnels_status(self) -> Dict[str, bool]:
        """Проверяет статус всех туннелей"""
        status = {}
        
        # Проверяем локальные форварды
        for forward in LOCAL_FORWARDS:
            local_port = int(forward.split(':')[0])
            status[f"local_{local_port}"] = self.test_port("localhost", local_port)
            
        return status
        
    def print_tunnel_status(self):
        """Выводит статус туннелей"""
        status = self.check_tunnels_status()
        print(f"\n[{time.strftime('%H:%M:%S')}] Статус туннелей:")
        
        for forward in LOCAL_FORWARDS:
            parts = forward.split(':')
            local_port = int(parts[0])
            remote_info = f"{parts[1]}:{parts[2]}"
            is_active = status.get(f"local_{local_port}", False)
            status_icon = "✓" if is_active else "✗"
            print(f"  {status_icon} L{local_port} -> {remote_info} ({'активен' if is_active else 'недоступен'})")
            
        for forward in REMOTE_FORWARDS:
            parts = forward.split(':')
            remote_port = int(parts[0])
            local_info = f"{parts[1]}:{parts[2]}"
            print(f"  → R{remote_port} <- {local_info} (удаленный форвард)")
            
    def run_connection(self) -> Optional[subprocess.Popen]:
        """Запускает SSH-соединение с туннелями"""
        cmd = self.build_ssh_command()
        
        print(f"[{time.strftime('%H:%M:%S')}] Подключаюсь к {SSH_USER}@{SSH_HOST}...")
        print(f"[{time.strftime('%H:%M:%S')}] Команда: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Ждем немного для установки соединения
            time.sleep(3)
            
            # Проверяем, что процесс еще работает
            if process.poll() is None:
                print(f"[{time.strftime('%H:%M:%S')}] Соединение установлено!")
                self.print_tunnel_status()
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"[{time.strftime('%H:%M:%S')}] Ошибка подключения:")
                if stderr:
                    print(f"STDERR: {stderr}")
                return None
                
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Ошибка запуска: {e}")
            return None
            
    def monitor_connection(self):
        """Мониторит соединение в отдельном потоке"""
        while self.running and self.process:
            time.sleep(30)  # Проверяем каждые 30 секунд
            if self.process.poll() is not None:
                break
            self.print_tunnel_status()
            
    def start(self):
        """Запускает менеджер туннелей"""
        def signal_handler(sig, frame):
            print("\n[CTRL+C] Завершение скрипта...")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        self.running = True
        
        print("=== SSH Bidirectional Tunnel Manager ===")
        print(f"Сервер: {SSH_USER}@{SSH_HOST}")
        print(f"Локальных форвардов: {len(LOCAL_FORWARDS)}")
        print(f"Удаленных форвардов: {len(REMOTE_FORWARDS)}")
        print("\nДля завершения нажмите Ctrl+C\n")
        
        while self.running:
            if MAX_RETRIES > 0 and self.retry_count >= MAX_RETRIES:
                print(f"[{time.strftime('%H:%M:%S')}] Превышено максимальное количество попыток ({MAX_RETRIES})")
                break
                
            self.process = self.run_connection()
            
            if self.process is None:
                print(f"[{time.strftime('%H:%M:%S')}] Не удалось установить соединение. Переподключение через {RETRY_DELAY}с...")
                time.sleep(RETRY_DELAY)
                self.retry_count += 1
                continue
                
            # Запускаем мониторинг в отдельном потоке
            monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
            monitor_thread.start()
            
            # Ждем завершения процесса
            try:
                return_code = self.process.wait()
                print(f"[{time.strftime('%H:%M:%S')}] Соединение разорвано (код: {return_code})")
            except KeyboardInterrupt:
                self.stop()
                break
                
            self.retry_count += 1
            if self.running:
                print(f"[{time.strftime('%H:%M:%S')}] Переподключение через {RETRY_DELAY}с... (попытка {self.retry_count})")
                time.sleep(RETRY_DELAY)
                
    def stop(self):
        """Останавливает менеджер"""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print(f"[{time.strftime('%H:%M:%S')}] Соединение закрыто")

def show_usage():
    """Показывает справку по использованию"""
    print("""
=== SSH Bidirectional Tunnel Manager ===

Использование:
  python3 ssh_bidirectional_tunnel.py [команда]

Команды:
  start    - Запустить туннели (по умолчанию)
  test     - Проверить доступность портов
  config   - Показать текущую конфигурацию
  help     - Показать эту справку

Примеры:
  python3 ssh_bidirectional_tunnel.py
  python3 ssh_bidirectional_tunnel.py start
  python3 ssh_bidirectional_tunnel.py test

Конфигурация:
  - Отредактируйте переменные в начале файла
  - LOCAL_FORWARDS: доступ к сервисам ВПС с локального компьютера
  - REMOTE_FORWARDS: доступ к локальным сервисам с ВПС
""")

def show_config():
    """Показывает текущую конфигурацию"""
    print("=== Текущая конфигурация ===")
    print(f"Сервер: {SSH_USER}@{SSH_HOST}")
    print(f"SSH ключ: {SSH_KEY}")
    print(f"Задержка переподключения: {RETRY_DELAY}с")
    print(f"Максимальное количество попыток: {MAX_RETRIES if MAX_RETRIES > 0 else 'Бесконечно'}")
    
    print("\nЛокальные форварды (L):")
    for forward in LOCAL_FORWARDS:
        parts = forward.split(':')
        print(f"  localhost:{parts[0]} -> {parts[1]}:{parts[2]}")
        
    print("\nУдаленные форварды (R):")
    for forward in REMOTE_FORWARDS:
        parts = forward.split(':')
        print(f"  {SSH_HOST}:{parts[0]} <- {parts[1]}:{parts[2]}")

def test_local_ports():
    """Тестирует доступность локальных портов"""
    print("=== Тестирование портов ===")
    
    # Тестируем локальные порты (где будут туннели)
    print("\nЛокальные порты для туннелей:")
    for forward in LOCAL_FORWARDS:
        local_port = int(forward.split(':')[0])
        is_available = not SSHTunnelManager().test_port("localhost", local_port)
        status = "свободен" if is_available else "занят"
        icon = "✓" if is_available else "⚠"
        print(f"  {icon} Порт {local_port}: {status}")
        
    # Тестируем подключение к серверу
    print(f"\nПодключение к серверу {SSH_HOST}:")
    is_reachable = SSHTunnelManager().test_port(SSH_HOST, 22)
    status = "доступен" if is_reachable else "недоступен" 
    icon = "✓" if is_reachable else "✗"
    print(f"  {icon} SSH порт 22: {status}")

def main():
    """Главная функция"""
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "help":
        show_usage()
    elif command == "config":
        show_config()
    elif command == "test":
        test_local_ports()
    elif command == "start":
        manager = SSHTunnelManager()
        manager.start()
    else:
        print(f"Неизвестная команда: {command}")
        print("Используйте 'help' для справки")
        sys.exit(1)

if __name__ == "__main__":
    main()