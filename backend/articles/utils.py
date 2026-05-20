from utils.common import resolve_upload

def upload_articles_image(instance, filename):
    return resolve_upload(instance.title, filename, 'articles')