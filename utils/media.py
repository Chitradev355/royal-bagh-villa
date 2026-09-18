import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from flask import current_app
from models import db, MediaFile

IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}
VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'm4v'}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def get_file_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def is_allowed_file(filename):
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


def get_media_type(filename):
    ext = get_file_extension(filename)
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    return 'image'


def format_file_size(bytes_size):
    if not bytes_size:
        return '0 B'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f'{bytes_size:.1f} {unit}'
        bytes_size /= 1024.0
    return f'{bytes_size:.1f} TB'


def save_uploaded_media(file, category='general', title=None, alt_text=None):
    if not file or not file.filename:
        return None, 'No file provided'

    if not is_allowed_file(file.filename):
        allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return None, f"File type not allowed. Supported types: {allowed_str}"

    original_name = secure_filename(file.filename) or 'upload'
    ext = get_file_extension(original_name)
    media_type = get_media_type(original_name)

    # Generate unique filename
    unique_name = f'{uuid.uuid4().hex[:12]}_{original_name}'

    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'media')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'video/mp4' if media_type == 'video' else 'image/jpeg'

    file_url = f'/static/uploads/media/{unique_name}'

    media = MediaFile(
        filename=unique_name,
        original_filename=original_name,
        file_url=file_url,
        file_type=media_type,
        mime_type=mime_type,
        file_size=file_size,
        title=title or original_name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title(),
        alt_text=alt_text or title or original_name,
        category=category
    )
    db.session.add(media)
    db.session.commit()

    return media, None


def delete_media_file(media_id):
    media = db.session.get(MediaFile, media_id)
    if not media:
        return False, 'Media not found'

    file_path = os.path.join(current_app.static_folder, 'uploads', 'media', media.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            pass

    db.session.delete(media)
    db.session.commit()
    return True, None
