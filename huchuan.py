import json
import time
import base64
import logging
import requests
import pyperclip
import random
import threading
import subprocess
import os
import sys
from datetime import datetime
from PIL import Image
import pystray
from pystray import MenuItem, Menu
import urllib.parse
iphone
# 简化日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f"sync_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)


class ClipboardSync:
    def __init__(self, config):
        self.base_url = config["base_url"].rstrip('/') + '/'
        self.config_url = self.base_url + config.get("config_file", "SyncClipboard.json")
        self.check_interval = config.get("check_interval", 2)
        self.notification_url = config.get("notification_url", "").strip()
        self.device_id = config.get("device_id", f"Device_{random.randint(100, 9999)}")

        # HTTP认证头
        auth = base64.b64encode(f"{config['username']}:{config['password']}".encode()).decode()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        })
        self.last_clipboard = ""
        self.last_etag = None
        self.last_random_number = 0
        self.running = True
        self.sync_thread = None
        self.tray_icon = None

    def get_cloud_data(self):
        """获取云端数据"""
        try:
            # 先发送HEAD请求获取ETag
            head_response = self.session.head(self.config_url, timeout=5)
            server_etag = head_response.headers.get("ETag")

            # 如果ETag存在且未改变，则不下载内容
            if server_etag and server_etag == self.last_etag:
                logging.debug("ETag未改变，跳过下载")
                return None

            # ETag改变或不存在，下载完整内容
            response = self.session.get(self.config_url, timeout=5)
            if response.status_code == 200:
                # 更新ETag
                if server_etag:
                    self.last_etag = server_etag
                
                data = response.json()
                return data
            else:
                return None
        except Exception as e:
            logging.error(f"获取云端数据异常: {e}")
            return None

    def upload_clipboard(self, content):
        """上传剪贴板到云端"""
        random_num = random.randint(0, 9999)
        data = {
            "Clipboard": content,
            "Type": "Text",
            "Device": self.device_id,
            "Random_number": str(random_num)
        }
        try:
            response = self.session.put(self.config_url, json=data, timeout=5)
            if response.status_code in [200, 204]:
                logging.info(f"上传成功: {content[:30]}...")
                return True
            else:
                logging.error(f"上传失败: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"上传异常: {e}")
            return False

    def sync_clipboard(self):
        """双向同步剪贴板"""
        try:
            current_clipboard = pyperclip.paste()

            # 本地剪贴板有变化 -> 上传
            if current_clipboard != self.last_clipboard and current_clipboard.strip():
                self.last_clipboard = current_clipboard
                self.send_notification("1")
                self.upload_clipboard(current_clipboard)
                return

            # 检查云端更新
            cloud_data = self.get_cloud_data()
            if not cloud_data:
                return

            cloud_random = cloud_data.get("Random_number", "0")
            cloud_device = cloud_data.get("Device", "") or cloud_data.get(" Device", "")
            cloud_content = cloud_data.get("Clipboard", "")
            cloud_type = cloud_data.get("Type", "") or cloud_data.get("type", "")

            try:
                cloud_random_int = int(cloud_random) if cloud_random else 0
            except (ValueError, TypeError):
                cloud_random_int = 0

            # 云端有其他设备的新内容 -> 下载
            if (cloud_random_int != self.last_random_number and
                    cloud_device.strip() != self.device_id and
                    cloud_content != self.last_clipboard and
                    cloud_content.strip() and
                    cloud_type.lower() == "text"):
                self.last_clipboard = cloud_content
                self.last_random_number = cloud_random_int
                pyperclip.copy(cloud_content)
                logging.info(f"下载: {cloud_content[:30]}... (来自设备: {cloud_device.strip()})")

        except Exception as e:
            logging.error(f"同步错误: {e}")

    def sync_loop(self):
        """同步循环线程"""
        logging.info(f"设备 {self.device_id} 开始同步")

        while self.running:
            try:
                self.sync_clipboard()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"同步循环异常: {e}")
                time.sleep(self.check_interval)

    def send_notification(self, content):
        """发送通知"""
        if not self.notification_url:
            return

        if not self.notification_url.startswith(('http://', 'https://')):
            logging.warning("通知URL必须以http://或https://开头")
            return

        try:
            url = self.notification_url.rstrip('/')
            logging.info(f"send_notification_url: {url}")

            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            payload = {
                "body": content,
                "title": "Cloud Clipboard",
                "badge": 1,
                "sound": "minuet",
                "group": "Clip"
            }

            # 重试机制
            for i in range(2):
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=5)
                    if resp.status_code == 200:
                        logging.info("通知发送成功")
                        break
                    else:
                        logging.warning(f"通知发送返回状态码: {resp.status_code}")
                except Exception as e:
                    if i == 1:
                        logging.error(f"通知发送失败 (重试后): {e}")
                    else:
                        logging.warning(f"通知发送失败 (正在重试): {e}")
        except Exception as e:
            logging.error(f"构建通知请求失败: {e}")

    def toggle_sync(self, icon, item):
        """切换同步状态"""
        if self.running:
            self.running = False
            logging.info("同步已暂停")
        else:
            self.running = True
            if self.sync_thread is None or not self.sync_thread.is_alive():
                self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
                self.sync_thread.start()
            logging.info("同步已开始")

        # 更新菜单
        self.update_menu()

    def open_config(self, icon, item):
        """打开配置文件"""
        # 修复配置文件路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe运行时
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_path = os.path.dirname(__file__)

        config_path = os.path.join(base_path, "config", "exchange_data.json")

        try:
            if os.path.exists(config_path):
                # Windows系统用记事本打开
                if sys.platform == "win32":
                    os.startfile(config_path)
                # macOS系统
                elif sys.platform == "darwin":
                    subprocess.call(["open", config_path])
                # Linux系统
                else:
                    subprocess.call(["xdg-open", config_path])
                logging.info(f"已打开配置文件: {config_path}")
            else:
                logging.error(f"配置文件不存在: {config_path}")
        except Exception as e:
            logging.error(f"打开配置文件失败: {e}")

    def quit_app(self, icon, item):
        """退出应用"""
        logging.info("正在退出应用...")
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
        icon.stop()
        sys.exit(0)

    def update_menu(self):
        """更新菜单"""
        if self.tray_icon:
            # 根据运行状态显示不同的菜单项
            sync_text = "状态：正在同步中" if self.running else "状态：暂停同步中"

            menu = Menu(
                MenuItem(sync_text, self.toggle_sync),
                MenuItem("配置文件", self.open_config),
                MenuItem("退出", self.quit_app)
            )

            self.tray_icon.menu = menu

    def load_icon(self):
        """加载图标文件"""
        # 确定基础路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe运行时
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_path = os.path.dirname(__file__)

        # 尝试多个可能的图标路径
        icon_paths = [
            os.path.join(base_path, "exchange.ico"),
            os.path.join(os.path.dirname(__file__), "exchange.ico"),
            "exchange.ico"
        ]

        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    image = Image.open(icon_path)
                    logging.info(f"成功加载图标: {icon_path}")
                    return image
                else:
                    logging.debug(f"图标文件不存在: {icon_path}")
            except Exception as e:
                logging.debug(f"加载图标失败 {icon_path}: {e}")

        # 所有路径都失败，创建默认图标
        logging.warning("无法加载exchange.ico，使用默认图标")
        return self.create_default_icon()

    def create_default_icon(self):
        """创建默认图标"""
        # 创建一个更好看的默认图标
        image = Image.new('RGBA', (16, 16), (70, 130, 180, 255))  # 钢蓝色
        return image

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 加载图标
        image = self.load_icon()

        # 创建初始菜单（根据初始运行状态）
        sync_text = "状态：正在同步中" if self.running else "状态：暂停同步中"

        menu = Menu(
            MenuItem(sync_text, self.toggle_sync),
            MenuItem("配置文件", self.open_config),
            MenuItem("退出", self.quit_app)
        )

        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "clipboard_sync",
            image,
            f"剪贴板同步 - {self.device_id}",
            menu
        )

        return self.tray_icon

    def run(self):
        """运行应用"""
        # 启动同步线程
        self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self.sync_thread.start()

        # 创建并运行托盘图标
        icon = self.create_tray_icon()
        logging.info("系统托盘图标已创建，右键查看菜单")
        icon.run()


def main():
    """主函数"""
    try:
        # 修复配置文件路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe运行时
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_path = os.path.dirname(__file__)

        config_path = os.path.join(base_path, "config", "exchange_data.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        logging.info(f"剪贴板同步服务启动")
        logging.info(f"设备ID: {config.get('device_id', '自动生成')}")

        sync = ClipboardSync(config)
        sync.run()

    except FileNotFoundError:
        logging.error(f"配置文件不存在: {config_path}")
        input("按回车键退出...")
    except json.JSONDecodeError as e:
        logging.error(f"配置文件格式错误: {e}")
        input("按回车键退出...")
    except Exception as e:
        logging.error(f"启动失败: {e}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()
