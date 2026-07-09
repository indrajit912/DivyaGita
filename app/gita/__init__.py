from flask import Blueprint

gita = Blueprint('gita', __name__)

from app.gita import routes
