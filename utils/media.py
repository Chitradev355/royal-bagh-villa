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

    # 1. Check for Cloudinary configuration
    cloudinary_url = current_app.config.get('CLOUDINARY_URL') or os.environ.get('CLOUDINARY_URL')
    cloudinary_cloud = current_app.config.get('CLOUDINARY_CLOUD_NAME') or os.environ.get('CLOUDINARY_CLOUD_NAME')
    
    if cloudinary_url or cloudinary_cloud:
        try:
            import cloudinary
            import cloudinary.uploader
            resource_type = "video" if media_type == 'video' else "image"
            upload_result = cloudinary.uploader.upload(
                file,
                resource_type=resource_type,
                folder="royal_bagh_villa"
            )
            file_url = upload_result.get('secure_url', upload_result.get('url'))
            file_size = upload_result.get('bytes', 0)
            mime_type = f"{media_type}/{ext}"
            unique_name = upload_result.get('public_id', f'cloud_{uuid.uuid4().hex[:12]}')

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
        except Exception as e:
            # Fall back to persistent/local disk if Cloudinary upload encounters an error
            file.seek(0)

    # 2. Local / Persistent Disk Storage (Render Disk or static folder)
    unique_name = f'{uuid.uuid4().hex[:12]}_{original_name}'
    upload_folder = current_app.config.get('MEDIA_UPLOAD_FOLDER')
    if not upload_folder:
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'media')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'video/mp4' if media_type == 'video' else 'image/jpeg'

    file_url = f'/uploads/media/{unique_name}'

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

    # Check Cloudinary deletion if remote
    if media.file_url and 'cloudinary.com' in media.file_url:
        try:
            import cloudinary
            import cloudinary.uploader
            resource_type = "video" if media.file_type == 'video' else "image"
            cloudinary.uploader.destroy(media.filename, resource_type=resource_type)
        except Exception:
            pass
    else:
        # Local or Persistent Disk removal
        upload_folder = current_app.config.get('MEDIA_UPLOAD_FOLDER')
        if not upload_folder:
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'media')
        file_path = os.path.join(upload_folder, media.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    db.session.delete(media)
    db.session.commit()
    return True, None
