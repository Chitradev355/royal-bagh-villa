import json
from datetime import datetime, timezone
from models import db


class CMSContent(db.Model):
    __tablename__ = 'cms_contents'

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(50), nullable=False, index=True)  # home, about, cafe, restaurant, events, banquet, lawn, gallery, contact, common
    section = db.Column(db.String(50), nullable=False, index=True)  # hero, intro, features, offers, pricing, seo, etc.
    key = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Text, default='')
    content_type = db.Column(db.String(20), default='text')  # text, html, image, video, url, json
    label = db.Column(db.String(200), default='')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('page', 'section', 'key', name='_page_section_key_uc'),
    )

    @classmethod
    def get_value(cls, page, key, default=''):
        item = cls.query.filter_by(page=page, key=key).first()
        if item and item.value is not None and item.value != '':
            return item.value
        return default

    @classmethod
    def set_value(cls, page, section, key, value, content_type='text', label=''):
        item = cls.query.filter_by(page=page, section=section, key=key).first()
        if item:
            item.value = value
            if content_type:
                item.content_type = content_type
            if label:
                item.label = label
        else:
            item = cls(page=page, section=section, key=key, value=value, content_type=content_type, label=label)
            db.session.add(item)
        db.session.commit()
        return item

    def __repr__(self):
        return f'<CMSContent {self.page}.{self.key}>'


class MediaFile(db.Model):
    __tablename__ = 'media_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    original_filename = db.Column(db.String(255), default='')
    file_url = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
    mime_type = db.Column(db.String(100), default='')
    file_size = db.Column(db.Integer, default=0)  # in bytes
    title = db.Column(db.String(255), default='')
    alt_text = db.Column(db.String(255), default='')
    category = db.Column(db.String(50), default='general')  # hero, cafe, restaurant, banquet, lawn, events, gallery, general
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'title': self.title or self.original_filename,
            'alt_text': self.alt_text,
            'category': self.category,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

    def __repr__(self):
        return f'<MediaFile {self.filename}>'


class CMSEvent(db.Model):
    __tablename__ = 'cms_events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(50), default='other')  # wedding, birthday, engagement, anniversary, corporate, party, kitty, other
    short_description = db.Column(db.Text, default='')
    full_description = db.Column(db.Text, default='')
    cover_image = db.Column(db.String(500), default='')
    video_url = db.Column(db.String(500), default='')
    features_json = db.Column(db.Text, default='[]')  # JSON array of features
    cta_label = db.Column(db.String(100), default='Plan Event')
    cta_link = db.Column(db.String(200), default='#enquiry')
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def features(self):
        try:
            return json.loads(self.features_json) if self.features_json else []
        except Exception:
            return []

    @features.setter
    def features(self, val):
        if isinstance(val, list):
            self.features_json = json.dumps(val)
        elif isinstance(val, str):
            # comma-separated string or json string
            try:
                self.features_json = json.dumps(json.loads(val))
            except Exception:
                items = [x.strip() for x in val.split('\n') if x.strip()] or [x.strip() for x in val.split(',') if x.strip()]
                self.features_json = json.dumps(items)
        else:
            self.features_json = '[]'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'category': self.category,
            'short_description': self.short_description,
            'full_description': self.full_description,
            'cover_image': self.cover_image,
            'video_url': self.video_url,
            'features': self.features,
            'cta_label': self.cta_label,
            'cta_link': self.cta_link,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<CMSEvent {self.title}>'


class GalleryItem(db.Model):
    __tablename__ = 'gallery_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), default='')
    caption = db.Column(db.String(255), default='')
    media_url = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(20), default='image')  # 'image' or 'video'
    category = db.Column(db.String(50), default='all')  # property, lawn, cafe, restaurant, events, food, all
    display_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'caption': self.caption,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'category': self.category,
            'display_order': self.display_order,
            'is_featured': self.is_featured
        }

    def __repr__(self):
        return f'<GalleryItem {self.title}>'


class NavigationItem(db.Model):
    __tablename__ = 'navigation_items'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(20), default='header')  # 'header', 'footer', 'both'
    display_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    is_external = db.Column(db.Boolean, default=False)
    target = db.Column(db.String(20), default='_self')

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'url': self.url,
            'location': self.location,
            'display_order': self.display_order,
            'is_visible': self.is_visible,
            'is_external': self.is_external,
            'target': self.target
        }

    def __repr__(self):
        return f'<NavigationItem {self.label}>'
