#!/usr/bin/env python3
import subprocess
import time
import sys
import signal
import os

# Параметры подключения
SSH_HOST = "31.59.58.96"
SSH_USER = "root"
SSH_KEY = f"{os.path.expanduser('~')}/.ssh/openssh_imported.key"
SSH_CMD = ["hpnssh", "-i", SSH_KEY, 
           "-o", "ConnectTimeout=10",
           "-o", "ServerAliveInterval=30",
           "-o", "ServerAliveCountMax=3",
           f"{SSH_USER}@{SSH_HOST}"]

# Параметры переподключения
RETRY_DELAY = 5  # Ждём 5 секунд перед переподключением
MAX_RETRIES = 0  # 0 = бесконечные попытки

def run_ssh_connection():
    """Запускает SSH-соединение"""
    print(f"[{time.strftime('%H:%M:%S')}] Подключаюсь к {SSH_USER}@{SSH_HOST}...")
    
    try:
        process = subprocess.Popen(
            SSH_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Ошибка запуска: {e}")
        return None

def main():
    """Основной цикл переподключения"""
    retry_count = 0
    
    def signal_handler(sig, frame):
        print("\n[CTRL+C] Завершение скрипта...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        if MAX_RETRIES > 0 and retry_count >= MAX_RETRIES:
            print(f"[{time.strftime('%H:%M:%S')}] Превышено максимальное количество попыток ({MAX_RETRIES})")
            break
        
        process = run_ssh_connection()
        
        if process is None:
            print(f"[{time.strftime('%H:%M:%S')}] Не удалось запустить процесс. Переподключение через {RETRY_DELAY}с...")
            time.sleep(RETRY_DELAY)
            retry_count += 1
            continue
        
        # Ждём завершения процесса
        try:
            return_code = process.wait()
            print(f"[{time.strftime('%H:%M:%S')}] Соединение разорвано (код: {return_code})")
        except KeyboardInterrupt:
            process.terminate()
            print("\n[CTRL+C] Соединение прервано вручную")
            break
        
        retry_count += 1
        print(f"[{time.strftime('%H:%M:%S')}] Переподключение через {RETRY_DELAY}с... (попытка {retry_count})")
        time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    main()