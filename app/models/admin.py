from flask_admin.contrib.sqla import ModelView
from flask import render_template, request, redirect, url_for
from flask_login import current_user
from config import Config

class AdminModelView(ModelView):
    def is_accessible(self):
        # Tylko zalogowani użytkownicy, którzy są adminami lub mają określony ID, mogą uzyskać dostęp
        return current_user.is_authenticated and (current_user.id == Config.admin_id or current_user.role == 'Admin')

    def inaccessible_callback(self, name, **kwargs):
        # Przekierowanie na stronę logowania, jeśli użytkownik nie ma dostępu
        return redirect(url_for('admin_login'))

class UserAdmin(AdminModelView):
    column_list = ('login', 'email', 'name', 'google_user', 'original_google_picture', 'about', 'picture', 'creation_date', 'last_login')
    column_filters = ('login', 'email', 'name', 'google_user', 'about')
    form_excluded_columns = ('password_hash',)

class FavoriteAdmin(AdminModelView):
    column_list = ('data', 'user_id', 'starred')
    column_filters = ('starred', 'user_id')

class NoteAdmin(AdminModelView):
    column_list = ('content', 'creation_date', 'favorite_id')
    column_filters = ('content', 'favorite_id')

class PostAdmin(AdminModelView):
    column_list = ('title', 'content', 'guest_author', 'creation_date', 'user_id')
    column_filters = ('title', 'content', 'guest_author', 'user_id')

class CommentAdmin(AdminModelView):
    column_list = ('content', 'guest_author', 'creation_date', 'user_id', 'post_id')
    column_filters = ('content', 'guest_author', 'user_id', 'post_id')

class NewsAdmin(AdminModelView):
    column_list = ('title', 'content', 'creation_date', 'user_id')
    column_filters = ('title', 'content', 'user_id')

class ReactionAdmin(AdminModelView):
    column_list = ('content', 'guest_author', 'creation_date', 'user_id', 'news_id')
    column_filters = ('content', 'guest_author', 'user_id', 'news_id')

class PostLikeItAdmin(AdminModelView):
    column_list = ('user_id', 'post_id')
    column_filters = ('user_id', 'post_id')

class PostHateItAdmin(AdminModelView):
    column_list = ('user_id', 'post_id')
    column_filters = ('user_id', 'post_id')

class CommentLikeItAdmin(AdminModelView):
    column_list = ('user_id', 'comment_id')
    column_filters = ('user_id', 'comment_id')

class CommentHateItAdmin(AdminModelView):
    column_list = ('user_id', 'comment_id')
    column_filters = ('user_id', 'comment_id')

class NewsLikeItAdmin(AdminModelView):
    column_list = ('user_id', 'news_id')
    column_filters = ('user_id', 'news_id')

class NewsHateItAdmin(AdminModelView):
    column_list = ('user_id', 'news_id')
    column_filters = ('user_id', 'news_id')

class ReactionLikeItAdmin(AdminModelView):
    column_list = ('user_id', 'reaction_id')
    column_filters = ('user_id', 'reaction_id')

class ReactionHateItAdmin(AdminModelView):
    column_list = ('user_id', 'reaction_id')
    column_filters = ('user_id', 'reaction_id')