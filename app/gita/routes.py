from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.gita import gita
from app.gita.forms import ExplanationForm
from app.models.gita import Chapter, Verse, Explanation, Translation
from app.models.user import User

@gita.route('/chapter/<int:chapter_num>')
def chapter_detail(chapter_num):
    """Displays a chapter details and a list of all its verses."""
    chapter = Chapter.query.filter_by(chapter_number=chapter_num).first_or_404()
    # Sort verses by verse_number
    verses = Verse.query.filter_by(chapter_id=chapter.id).order_by(Verse.verse_number).all()
    
    # Get previous and next chapters for navigation
    prev_chapter = Chapter.query.filter_by(chapter_number=chapter_num - 1).first()
    next_chapter = Chapter.query.filter_by(chapter_number=chapter_num + 1).first()
    
    return render_template(
        'gita/chapter_detail.html',
        chapter=chapter,
        verses=verses,
        prev_chapter=prev_chapter,
        next_chapter=next_chapter
    )

@gita.route('/verse/<int:chapter_num>/<int:verse_num>', methods=['GET', 'POST'])
def verse_detail(chapter_num, verse_num):
    """Displays a verse, its default translation, and community explanations."""
    chapter = Chapter.query.filter_by(chapter_number=chapter_num).first_or_404()
    verse = Verse.query.filter_by(chapter_id=chapter.id, verse_number=verse_num).first_or_404()
    
    # Get default translation
    default_translation = Translation.query.filter_by(verse_id=verse.id, author='Default').first()
    
    # Get community explanations ordered by creation date
    explanations = Explanation.query.filter_by(verse_id=verse.id).order_by(Explanation.created_at.desc()).all()
    
    # Form for adding/editing explanations
    form = ExplanationForm()
    
    # Check if current user already has an explanation
    user_explanation = None
    if current_user.is_authenticated:
        user_explanation = Explanation.query.filter_by(verse_id=verse.id, user_id=current_user.id).first()
        if request.method == 'GET' and user_explanation:
            form.content.data = user_explanation.content

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You must be logged in to contribute explanations.", "danger")
            return redirect(url_for('auth.login'))
            
        if user_explanation:
            # Update existing explanation
            user_explanation.content = form.content.data
            flash("Your explanation has been updated successfully!", "success")
        else:
            # Create a new explanation
            new_explanation = Explanation(
                verse_id=verse.id,
                user_id=current_user.id,
                content=form.content.data
            )
            db.session.add(new_explanation)
            flash("Thank you for contributing your explanation!", "success")
            
        db.session.commit()
        return redirect(url_for('gita.verse_detail', chapter_num=chapter_num, verse_num=verse_num))
        
    # Setup pagination/navigation links
    # Find total verses in this chapter
    total_verses = chapter.verses_count
    prev_verse_num = verse_num - 1 if verse_num > 1 else None
    next_verse_num = verse_num + 1 if verse_num < total_verses else None
    
    return render_template(
        'gita/verse_detail.html',
        chapter=chapter,
        verse=verse,
        default_translation=default_translation,
        explanations=explanations,
        form=form,
        user_explanation=user_explanation,
        prev_verse_num=prev_verse_num,
        next_verse_num=next_verse_num
    )

@gita.route('/explanation/<int:explanation_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_explanation(explanation_id):
    """Standalone page/route to edit an explanation (optional alternate route)."""
    explanation = Explanation.query.get_or_404(explanation_id)
    
    # Verify authorization: Owner or Admin
    if explanation.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    form = ExplanationForm()
    if request.method == 'GET':
        form.content.data = explanation.content
        
    if form.validate_on_submit():
        explanation.content = form.content.data
        db.session.commit()
        flash("Explanation updated successfully.", "success")
        return redirect(url_for('gita.verse_detail', 
                                chapter_num=explanation.verse.chapter.chapter_number, 
                                verse_num=explanation.verse.verse_number))
                                
    return render_template('gita/edit_explanation.html', form=form, explanation=explanation)

@gita.route('/explanation/<int:explanation_id>/delete', methods=['POST'])
@login_required
def delete_explanation(explanation_id):
    """Deletes an explanation. Available to the owner and administrators."""
    explanation = Explanation.query.get_or_404(explanation_id)
    chapter_num = explanation.verse.chapter.chapter_number
    verse_num = explanation.verse.verse_number
    
    # Verify authorization: Owner or Admin
    if explanation.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to delete this explanation.", "danger")
        return redirect(url_for('gita.verse_detail', chapter_num=chapter_num, verse_num=verse_num))
        
    db.session.delete(explanation)
    db.session.commit()
    flash("Explanation deleted successfully.", "info")
    return redirect(url_for('gita.verse_detail', chapter_num=chapter_num, verse_num=verse_num))
