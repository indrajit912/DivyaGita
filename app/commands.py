import os
import json
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import Role, User
from app.models.gita import Chapter, Verse, Translation, Reference

@click.command('setup-db')
@with_appcontext
def setup_db_command():
    """Create database tables and populate Bhagavad Gita data."""
    click.echo("Initializing database tables...")
    db.create_all()
    
    # 1. Seed Roles
    click.echo("Seeding roles...")
    admin_role = Role.query.filter_by(name='Administrator').first()
    if not admin_role:
        admin_role = Role(name='Administrator', description='System Administrator with moderation privileges')
        db.session.add(admin_role)
        
    user_role = Role.query.filter_by(name='Standard User').first()
    if not user_role:
        user_role = Role(name='Standard User', description='Registered contributor who can write explanations')
        db.session.add(user_role)
        
    db.session.commit()
    
    # 2. Seed Chapters
    click.echo("Seeding chapters from data/chapters.json...")
    base_dir = os.path.dirname(os.path.dirname(__file__))
    chapters_file = os.path.join(base_dir, 'data', 'chapters.json')
    
    if not os.path.exists(chapters_file):
        click.echo(f"Error: {chapters_file} not found. Please run fetch_gita_data.py first.")
        return
        
    with open(chapters_file, 'r', encoding='utf-8') as f:
        chapters_data = json.load(f)
        
    for ch in chapters_data:
        existing_ch = Chapter.query.filter_by(chapter_number=ch['chapter_number']).first()
        if not existing_ch:
            new_ch = Chapter(
                chapter_number=ch['chapter_number'],
                verses_count=ch['verses_count'],
                name=ch['name'],
                translation=ch['translation'],
                transliteration=ch['transliteration'],
                meaning=ch['meaning']['en'],
                summary=ch['summary']['en']
            )
            db.session.add(new_ch)
            
    db.session.commit()
    click.echo("Chapters seeded successfully.")
    
    # 3. Seed Verses, Translations, and References
    click.echo("Seeding verses from data/verses.json...")
    verses_file = os.path.join(base_dir, 'data', 'verses.json')
    
    if not os.path.exists(verses_file):
        click.echo(f"Error: {verses_file} not found. Please run fetch_gita_data.py first.")
        return
        
    with open(verses_file, 'r', encoding='utf-8') as f:
        verses_data = json.load(f)
        
    count = 0
    for v in verses_data:
        chapter = Chapter.query.filter_by(chapter_number=v['chapter_number']).first()
        if not chapter:
            click.echo(f"Warning: Chapter {v['chapter_number']} not found. Skipping verse.")
            continue
            
        existing_v = Verse.query.filter_by(chapter_id=chapter.id, verse_number=v['verse_number']).first()
        if not existing_v:
            new_v = Verse(
                chapter_id=chapter.id,
                verse_number=v['verse_number'],
                sanskrit=v['sanskrit'],
                transliteration=v['transliteration']
            )
            db.session.add(new_v)
            db.session.flush()  # get the ID of the newly added verse
            
            # Add translation
            new_t = Translation(
                verse_id=new_v.id,
                author='Default',
                content=v['translation']
            )
            db.session.add(new_t)
            
            # Add reference
            if v.get('reference'):
                new_ref = Reference(
                    verse_id=new_v.id,
                    content=v['reference']
                )
                db.session.add(new_ref)
                
            count += 1
            if count % 100 == 0:
                db.session.commit()
                click.echo(f"Seeded {count} verses...")
                
    db.session.commit()
    click.echo(f"Successfully seeded {count} verses, translations, and references.")
    click.echo("Database setup complete!")

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create an administrator account interactively."""
    click.echo("=== Create Administrator Account ===")
    
    username = click.prompt("Username").strip()
    email = click.prompt("Email").strip()
    name = click.prompt("Full Name").strip()
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    
    # Verify administrator role exists
    admin_role = Role.query.filter_by(name='Administrator').first()
    if not admin_role:
        click.echo("Error: Roles have not been seeded yet. Please run 'flask setup-db' first.")
        return
        
    # Check if user already exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        click.echo("Error: A user with that username or email already exists.")
        return
        
    admin_user = User(
        username=username,
        email=email,
        name=name,
        role_id=admin_role.id,
        is_active=True,
        is_email_verified=True  # Admins are pre-verified
    )
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    click.echo(f"Administrator '{username}' created successfully!")
