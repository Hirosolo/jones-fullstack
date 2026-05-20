# path: utils/function.py

from utils.common import resolve_upload

def upload_articles_image(instance, filename):
    return resolve_upload(instance.title, filename, 'articles')

def upload_home_slider_image(instance, filename):
    return resolve_upload(instance.title, filename, 'slider')

def upload_static_page_image(instance, filename):
    return resolve_upload(instance.title, filename, 'static_page')