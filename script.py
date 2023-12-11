import os
import glob
import json
import shutil
import winreg
import platform
import subprocess
import mysql.connector

from datetime import datetime


db_config = {
    'host': os.environ.get('DB_HOST', 'default_host'),
    'database': os.environ.get('DB_DATABASE', 'default_database'),
    'user': os.environ.get('DB_USER', 'default_user'),
    'password': os.environ.get('DB_PASSWORD', 'default_password')
}


def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except subprocess.CalledProcessError:
        return None


def is_windows_activated():
    result = execute_command('cscript //Nologo slmgr.vbs /xpr')
    return 'activated' in result.lower() if result else 'not activated'


def is_office_activated():
    result = get_office_version()
    return 'activated' if result != 'Unknown' else 'not activated'


def get_special_folder_path(folder_name):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    folder_path, _ = winreg.QueryValueEx(key, folder_name)
    winreg.CloseKey(key)
    return folder_path


def is_installed(app_name):
    try:
        subprocess.check_output(f'where {app_name}', stderr=subprocess.DEVNULL, shell=True, text=True)
        return 'Installed'
    except subprocess.CalledProcessError:
        return 'Not Installed'


def get_office_version():
    command = 'reg query "HKLM\\Software\\Microsoft\\Office\\ClickToRun\\Configuration" /v VersionToReport'
    result = execute_command(command)
    if result:
        split_result = result.split()
        if len(split_result) >= 3:
            return split_result[-1]
    return 'Unknown'


def find_mail_configs():
    mail_configs = []
    for drive in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if os.path.exists(f'{drive}:'):
            for file in glob.glob(f'{drive}:/**/*.msf', recursive=True):
                folder_name = os.path.basename(os.path.dirname(file))
                mail_configs.append(f"Folder: {folder_name}, Path: {file}")
    return ', '.join(mail_configs)


def gather_system_info():
    user = os.environ.get('USERNAME', 'N/A')
    computer_name = platform.node()
    my_documents = get_special_folder_path('Personal')
    downloads = get_special_folder_path('{374DE290-123F-4565-9164-39C4925E467B}')
    pictures = get_special_folder_path('My Pictures')
    whats_app_installed = is_installed('WhatsApp')
    we_chat_installed = is_installed('WeChat')
    thunderbird_installed = is_installed('Thunderbird')
    windows_version = platform.version()
    office_version = get_office_version()
    windows_activated = is_windows_activated()
    office_activated = is_office_activated()

    disk_info = []
    for drive in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if os.path.exists(f'{drive}:'):
            total, used, free = shutil.disk_usage(f'{drive}:')
            disk_info.append({
                'disk_label': f'{drive}:',
                'total_size_gb': total // (1024 ** 3),
                'free_space_gb': free // (1024 ** 3)
            })

    user_profiles = []
    profiles_path = os.path.expanduser('C:/Users')
    for profile in os.listdir(profiles_path):
        profile_path = os.path.join(profiles_path, profile)
        if os.path.isdir(profile_path) and profile not in ['Default', 'Public', 'Default User']:
            size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames, filenames in
                       os.walk(profile_path) for filename in filenames)
            user_profiles.append({
                'username': profile,
                'folder_size_gb': size // (1024 ** 3)
            })

    return {
        'user': user,
        'computer_name': computer_name,
        'my_documents': my_documents,
        'downloads': downloads,
        'pictures': pictures,
        'whats_app_installed': whats_app_installed,
        'we_chat_installed': we_chat_installed,
        'thunderbird_installed': thunderbird_installed,
        'windows_version': windows_version,
        'office_version': office_version,
        'disk_info_json': json.dumps(disk_info),
        'user_profiles_json': json.dumps(user_profiles),
        'windows_activated': windows_activated,
        'office_activated': office_activated
    }


def write_log(event_type, username, status, details=""):
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            log_query = """
                INSERT INTO file_logs (EventTime, EventType, UserName, Status, Details) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(log_query, (datetime.now(), event_type, username, status, details))
            connection.commit()
    except mysql.connector.Error as error:
        print(f"Failed to write log to MySQL table: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def insert_data_into_db(data):
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()

            user_query = """
                INSERT INTO user_info (UserLogin, ComputerName, MyDocuments, Downloads, Pictures, 
                    WhatsAppInstalled, WeChatInstalled, ThunderbirdInstalled, WindowsVersion, OfficeVersion, 
                    DiskInfo, UserProfiles) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    ComputerName = VALUES(ComputerName), MyDocuments = VALUES(MyDocuments), 
                    Downloads = VALUES(Downloads), Pictures = VALUES(Pictures), 
                    WhatsAppInstalled = VALUES(WhatsAppInstalled), WeChatInstalled = VALUES(WeChatInstalled), 
                    ThunderbirdInstalled = VALUES(ThunderbirdInstalled), WindowsVersion = VALUES(WindowsVersion), 
                    OfficeVersion = VALUES(OfficeVersion), DiskInfo = VALUES(DiskInfo), 
                    UserProfiles = VALUES(UserProfiles);
            """
            cursor.execute(user_query, (data['user'], data['computer_name'], data['my_documents'], data['downloads'],
                                        data['pictures'], data['whats_app_installed'], data['we_chat_installed'],
                                        data['thunderbird_installed'],
                                        data['windows_version'], data['office_version'], data['disk_info_json'],
                                        data['user_profiles_json']))
            mail_configs = find_mail_configs()
            update_query = "UPDATE user_info SET MailConfigs = %s WHERE UserLogin = %s"
            cursor.execute(update_query, (mail_configs, data['user']))
            now = datetime.now()
            update_time_query = "UPDATE user_info SET LastUpdated = %s WHERE UserLogin = %s"
            cursor.execute(update_time_query, (now, data['user']))
            update_query = """
                   UPDATE user_info SET WinActivate = %s, OfficeActivate = %s WHERE UserLogin = %s
                   """
            cursor.execute(update_query, (data['windows_activated'], data['office_activated'], data['user']))

            connection.commit()
            write_log("Data Insertion", data['user'], "Success", "Details of the operation")
    except mysql.connector.Error as error:
        write_log("Data Insertion", data['user'], "Error", str(error))
        print(f"Failed to insert record into MySQL table: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    system_info = gather_system_info()
    insert_data_into_db(system_info)
