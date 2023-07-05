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
        print(f'{timelog}: Токен VK принят.')

    def get_photos_url(self, vk_id, album_id='profile'):
        """Метод возвращает список фотографий для скачивания на Яндекс диск. По умолчанию из альбома профиля."""
        get_photos_url = self.url + 'photos.get'
        params = {
            'owner_id': vk_id,
            'album_id': album_id,
            'rev': 1,
            'extended': 1
        }
        req = requests.get(get_photos_url, params={**self.params, **params})
        if 200 <= req.status_code < 300:
            if 'response' in req.json().keys():
                name_foto_list = []
                photo_list_for_upload = []
                for file in req.json()['response']['items']:
                    types = []
                    name_photo = str(file['likes']['count']) + '.jpg'
                    date = '-' + str(file['date'])
                    if name_photo not in name_foto_list:
                        name_foto_list.append(name_photo)
                    else:
                        name_photo += date
                        name_foto_list.append(name_photo)
                    for size in file['sizes']:
                        types.append(size['type'])
                    types_sorted = sorted(types, key=lambda x: x == 'w')
                    for size in file['sizes']:
                        if size['type'] == types_sorted[-1]:
                            photo_list_for_upload.append({'url': size['url'], 'size': size['type'], 'name': name_photo})
                print(f'{timelog}: Список фотографий для скачивания получен.')
                return photo_list_for_upload
            else:
                print(f'{timelog}: Введен некорректный Id пользователя! Фотографии не будут загружены')
        elif 400 <= req.status_code < 499:
            print(f'{timelog}: Ошибка на стороне клиента!')
        elif 500 <= req.status_code:
            print(f'{timelog}: Ошибка на стороне сервера!')
        else:
            print(f'{timelog}: Ошибка. Что-то пошло не так!')


class YaUploader:
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, token):
        self.token = token
        print(f'{timelog}: Токен Полигона принят.')

    def upload(self, path_to_photo, count=5):
        """метод создает папку на Яндекс диске и загружает фотографии из списка в эту папку.
        По умолчанию 5 фотографий"""
        url_new_folder = 'https://cloud-api.yandex.net/v1/disk/resources'
        folder = input('Придумайте название новой папки для загруженных фотографий! ')
        req = requests.put(url_new_folder, params={'path': f'/{folder}'}, headers={'Authorization': token_ya})
        if 200 <= req.status_code < 300:
            print(f'{timelog}: Папка {folder} создана.')
            uploaded_photos = []
            if type(path_to_photo) == list:
                for file in tqdm(path_to_photo[:count]):
                    time.sleep(0.33)
                    params = {
                        'url': file['url'],
                        'path': f"/{folder}/{file['name']}"
                    }
                    headers = {'Authorization': token_ya}
                    r = requests.post(self.url, params=params, headers=headers)
                    if 200 <= r.status_code < 300:
                        uploaded_photos.append({'file_name': file['name'], 'size': file['size']})
                    else:
                        print(f'{timelog}: Не удалось загрузить фотографию!')
                with open('UploadedPhotos.json', 'w') as f:
                    json.dump(uploaded_photos, f, ensure_ascii=False, indent=2)
                print(f'{timelog}: Фотографии загружены на Яндекс диск!')
            else:
                print(f'{timelog}: Фотографии не загружены!')
        elif 400 <= req.status_code < 499:
            print(f'{timelog}: Папка не создана. Фотографии не загружены. Ошибка на стороне клиента!')
        elif 500 <= req.status_code:
            print(f'{timelog}: Папка не создана. Фотографии не загружены. Ошибка на стороне сервера!')
        else:
            print(f'{timelog}: Папка не создана. Фотографии не загружены!')


def download_photos(photo_url_list, path_on_pc, count=5):
    """Функция скачивает фотографии по списку URLов на жесткий диск по заданному пути. По умолчанию 5 штук."""
    for photo in tqdm(photo_url_list[:count]):
        time.sleep(0.33)
        wget.download(photo['url'], fr"{path_on_pc}\{photo['name']}")
    print(f'{timelog}: Фотографии скачены!')


def upload_on_gdrive_from_url(photo_url_list, count=5):
    """Функция создает папку на Google диске и загружает фотографии из списка в эту папку.
    По умолчанию 5 фотографий. Нужен файл client_secrets.json"""
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    folder_name = input('Придумайте название новой папки для загруженных фотографий! ')
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    folder_id = folder['id']
    uploaded_photos = []
    if type(photo_url_list) == list:
        for file in tqdm(photo_url_list[:count]):
            time.sleep(0.33)
            metadata = {
                'name': file['name'],
                'parents': [folder_id]
            }
            files = {
                'data': ('metadata', json.dumps(metadata), 'application/json'),
                'file': io.BytesIO(requests.get(file['url']).content)
            }
            r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
                              headers={'Authorization': 'Bearer ' + gauth.credentials.access_token}, files=files)
            if 200 <= r.status_code < 300:
                uploaded_photos.append({'file_name': file['name'], 'size': file['size']})
            elif 400 <= r.status_code < 499:
                print(f'{timelog}: Ошибка на стороне клиента!')
            elif 500 <= r.status_code:
                print(f'{timelog}: Ошибка на стороне сервера!')
            else:
                print('Не удалось загрузить фотографию!')
        with open('UploadedPhotos.json', 'w') as f:
            json.dump(uploaded_photos, f, ensure_ascii=False, indent=2)
        print(f'{timelog}: Фотографии загружены на Google диск!')
    else:
        print(f'{timelog}: Фотографии не загружены!')


if __name__ == '__main__':
    timelog = time.ctime(time.time())
    tokenvk = '...'
    vk_client = VkUser(tokenvk, '5.131')
    photo_list_path = vk_client.get_photos_url(input('Введите Id пользователя: '))
    # download_photos(photo_list_path, input('Введите путь до папки, в которую нужно скачать фотографии: '))
    token_ya = input('Введите токен с Полигона Яндекс.Диска: ')
    ya_client = YaUploader(token_ya)
    ya_client.upload(photo_list_path)
    # upload_on_gdrive_from_url(photo_list_path)
