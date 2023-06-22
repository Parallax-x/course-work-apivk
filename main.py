import json
import requests
import time
import wget
import io
from tqdm import tqdm
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token_vk, version):
        self.params = {
            'access_token': token_vk,
            'v': version
        }
        print(f'{time.ctime(time.time())}: Токен VK принят.')

    def get_photos_url(self, vk_id, album_id='profile'):
        """Метод возвращает список фотографий со всеми атрибутами для скачивания на Яндекс диск.
         По умолчанию из альбома профиля."""
        get_photos_url = self.url + 'photos.get'
        params = {
            'owner_id': vk_id,
            'album_id': album_id,
            'rev': 1,
            'extended': 1
        }
        req = requests.get(get_photos_url, params={**self.params, **params}).json()
        photo_list = req['response']['items']
        print(f'{time.ctime(time.time())}: Список фотографий c атрибутами для скачивания получен.')
        return photo_list

    def get_only_photos_url(self, vk_id, album_id='profile'):
        """Метод возвращает список фотографий максимального размера для скачивания на жесткий диск.
        По умолчанию из альбома профиля."""
        get_photos_url = self.url + 'photos.get'
        params = {
            'owner_id': vk_id,
            'album_id': album_id,
            'rev': 1,
            'extended': 1
        }
        req = requests.get(get_photos_url, params={**self.params, **params}).json()
        photo_list = req['response']['items']
        max_url_list = []
        for file in photo_list:
            types = []
            for size in file['sizes']:
                types.append(size['type'])
            types_sorted = sorted(types, key=lambda x: x == 'w')
            for size in file['sizes']:
                if size['type'] == types_sorted[-1]:
                    max_url_list.append(size['url'])
        print(f'{time.ctime(time.time())}: Список URLов фотографий для скачивания получен.')
        return max_url_list


class YaUploader:
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, token):
        self.token = token
        print(f'{time.ctime(time.time())}: Токен Полигона принят.')

    def upload(self, path_to_photo, count=5):
        """метод создает папку PhotosVk на Яндекс диске и загружает фотографии из списка в эту папку.
        По умолчанию 5 фотографий"""
        url_new_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        requests.put(url_new_folder, params={'path': '/PhotosVk'}, headers={'Authorization': token_ya})
        print('Папка PhotosVk создана.')
        name_foto_list = []
        uploaded_photos = []
        for file in tqdm(path_to_photo[:count]):
            time.sleep(0.33)
            types = []
            url_photo_max = str
            max_size = str
            for size in file['sizes']:
                types.append(size['type'])
            types_sorted = sorted(types, key=lambda x: x == 'w')
            for size in file['sizes']:
                if size['type'] == types_sorted[-1]:
                    url_photo_max = size['url']
                    max_size = size['type']
            name_photo = str(file['likes']['count']) + '.jpg'
            date = '-' + str(file['date'])
            if name_photo not in name_foto_list:
                name_foto_list.append(name_photo)
                uploaded_photos.append({'file_name': name_photo, 'size': max_size})
            else:
                name_photo += date
                name_foto_list.append(name_photo)
                uploaded_photos.append({'file_name': name_photo, 'size': max_size})
            params = {
                'url': url_photo_max,
                'path': f'/PhotosVk/{name_photo}'
            }
            headers = {'Authorization': token_ya}
            requests.post(self.url, params=params, headers=headers)
        with open('UploadedPhotos.json', 'w') as f:
            json.dump(uploaded_photos, f, ensure_ascii=False, indent=2)
        print(f'{time.ctime(time.time())}: Все фотографии скачены на Яндекс диск!')


def download_photos(photo_url_list, path_on_pc, count=5):
    """Функция скачивает фотографии по списку URLов на жесткий диск по заданному пути. По умолчанию 5 штук.
    Название из URL"""
    for photo in tqdm(photo_url_list[:count]):
        time.sleep(0.33)
        name = photo.split('/')[-1].split('?')[0]
        wget.download(photo, fr'{path_on_pc}\{name}')
    print(f'{time.ctime(time.time())}: Все фотографии скачены!')


def download_photos_from_vk(photo_url_list, path_on_pc, count=5):
    """Функция скачивает фотографии по списку с атрибутами на жесткий диск по заданному пути. По умолчанию 5 штук.
    Название фотографии - количество лайков."""
    name_foto_list = []
    for file in tqdm(photo_url_list[:count]):
        time.sleep(0.33)
        types = []
        url_photo_max = str
        for size in file['sizes']:
            types.append(size['type'])
        types_sorted = sorted(types, key=lambda x: x == 'w')
        for size in file['sizes']:
            if size['type'] == types_sorted[-1]:
                url_photo_max = size['url']
        name_photo = str(file['likes']['count']) + '.jpg'
        date = '-' + str(file['date'])
        if name_photo not in name_foto_list:
            name_foto_list.append(name_photo)
        else:
            name_photo += date
            name_foto_list.append(name_photo)
        wget.download(url_photo_max, fr'{path_on_pc}\{name_photo}')
    print(f'{time.ctime(time.time())}: Все фотографии скачены!')


def upload_on_gdrive_from_url(photo_url_list, count=5):
    """Функция создает папку PhotosVk на Google диске и загружает фотографии из списка в эту папку.
    По умолчанию 5 фотографий. Нужен файл client_secrets.json"""
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    folder_name = 'PhotosVk'
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    folder_id = folder['id']
    name_foto_list = []
    uploaded_photos = []
    for file in tqdm(photo_url_list[:count]):
        time.sleep(0.33)
        types = []
        url_photo_max = str
        max_size = str
        for size in file['sizes']:
            types.append(size['type'])
        types_sorted = sorted(types, key=lambda x: x == 'w')
        for size in file['sizes']:
            if size['type'] == types_sorted[-1]:
                url_photo_max = size['url']
                max_size = size['type']
        name_photo = str(file['likes']['count']) + '.jpg'
        date = '-' + str(file['date'])
        if name_photo not in name_foto_list:
            name_foto_list.append(name_photo)
            uploaded_photos.append({'file_name': name_photo, 'size': max_size})
        else:
            name_photo += date
            name_foto_list.append(name_photo)
            uploaded_photos.append({'file_name': name_photo, 'size': max_size})
        metadata = {
            'name': name_photo,
            'parents': [folder_id]
        }
        files = {
            'data': ('metadata', json.dumps(metadata), 'application/json'),
            'file': io.BytesIO(requests.get(url_photo_max).content)
        }
        requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
                      headers={'Authorization': 'Bearer ' + gauth.credentials.access_token}, files=files)
    with open('UploadedPhotos.json', 'w') as f:
        json.dump(uploaded_photos, f, ensure_ascii=False, indent=2)
    print(f'{time.ctime(time.time())}: Все фотографии скачены на Google диск!')


if __name__ == '__main__':
    tokenvk = '...'
    vk_client = VkUser(tokenvk, '5.131')
    # photo_list_url = vk_client.get_only_photos_url(input('Введите Id пользователя: '))
    photo_list_path = vk_client.get_photos_url(input('Введите Id пользователя: '))
    # download_photos(photo_list_url, input('Введите путь до папки, в которую нужно скачать фотографии: '))
    # download_photos_from_vk(photo_list_path, input('Введите путь до папки, в которую нужно скачать фотографии: '))
    token_ya = input('Введите токен с Полигона Яндекс.Диска: ')
    ya_client = YaUploader(token_ya)
    ya_client.upload(photo_list_path)
    # upload_on_gdrive_from_url(photo_list_path)
