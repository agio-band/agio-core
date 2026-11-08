import os

PUBLIC_URL = (os.getenv('AGIO_PUBLIC_BASE_URL') or 'https://s3.ru-7.storage.selcloud.ru/agio-public').rstrip('/')