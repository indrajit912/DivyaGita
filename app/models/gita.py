from datetime import datetime, timezone
from app.extensions import db

class Chapter(db.Model):
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_number = db.Column(db.Integer, unique=True, nullable=False)
    verses_count = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Sanskrit name
    translation = db.Column(db.String(150), nullable=False)  # English transliterated
    transliteration = db.Column(db.String(150), nullable=False)
    meaning = db.Column(db.String(255), nullable=False)  # English meaning
    summary = db.Column(db.Text, nullable=False)  # English summary
    
    verses = db.relationship('Verse', back_populates='chapter', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Chapter {self.chapter_number}: {self.translation}>"

class Verse(db.Model):
    __tablename__ = 'verses'
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    verse_number = db.Column(db.Integer, nullable=False)
    sanskrit = db.Column(db.Text, nullable=False)
    transliteration = db.Column(db.Text, nullable=False)
    
    chapter = db.relationship('Chapter', back_populates='verses')
    translations = db.relationship('Translation', back_populates='verse', cascade='all, delete-orphan')
    explanations = db.relationship('Explanation', back_populates='verse', cascade='all, delete-orphan')
    references = db.relationship('Reference', back_populates='verse', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('chapter_id', 'verse_number', name='_chapter_verse_uc'),
    )

    def __repr__(self):
        return f"<Verse {self.chapter.chapter_number if self.chapter else self.chapter_id}.{self.verse_number}>"

class Translation(db.Model):
    __tablename__ = 'translations'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False, default='Default')
    content = db.Column(db.Text, nullable=False)
    
    verse = db.relationship('Verse', back_populates='translations')

    def __repr__(self):
        return f"<Translation by {self.author} for Verse {self.verse_id}>"

class Explanation(db.Model):
    __tablename__ = 'explanations'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    verse = db.relationship('Verse', back_populates='explanations')
    user = db.relationship('User', back_populates='explanations')

    def __repr__(self):
        return f"<Explanation by User {self.user_id} for Verse {self.verse_id}>"

class Reference(db.Model):
    __tablename__ = 'references'
    
    id = db.Column(db.Integer, primary_key=True)
    verse_id = db.Column(db.Integer, db.ForeignKey('verses.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    
    verse = db.relationship('Verse', back_populates='references')

    def __repr__(self):
        return f"<Reference for Verse {self.verse_id}: {self.content}>"
