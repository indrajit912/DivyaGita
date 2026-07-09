from flask import render_template
from app.main import main
from app.models.gita import Chapter

@main.route('/')
def index():
    """Renders the landing page listing all chapters of the Bhagavad Gita."""
    chapters = Chapter.query.order_by(Chapter.chapter_number).all()
    return render_template('main/index.html', chapters=chapters)

@main.route('/about')
def about():
    """Renders the About page containing system details, developer background, and Gita overview."""
    return render_template('main/about.html')
