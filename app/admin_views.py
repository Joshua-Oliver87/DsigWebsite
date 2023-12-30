from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import flash
from flask_login import current_user, LoginManager
from sqlalchemy import func
from .Model.models import User
from .Model.database import db
from flask_admin.model.template import macro

# Custom view for the User model
class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

# Custom index view to protect the admin dashboard
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

class UserAdminView(ModelView):
    column_formatters = {
        'is_approved': macro('render_approve_column')
    }

    column_filters = ['is_approved']
    column_list = ('username', 'email', 'is_admin', 'is_approved')

    # Action to approve users
    @action('approve', 'Approve', 'Are you sure you want to approve selected users?')
    def action_approve(self, ids):
        try:
            query = User.query.filter(User.id.in_(ids))
            count = 0
            for user in query.all():
                if not user.is_approved:
                    user.is_approved = True
                    count += 1
            db.session.commit()
            flash(f'{count} users have been successfully approved.')
        except Exception as e:
            if not self.handle_view_exception(e):
                raise

            flash(f'Failed to approve users. Error: {str(e)}', 'error')

    def handle_view_exception(self, exc):
        return super(UserAdminView, self).handle_view_exception(exc)

    #To prevent access to this view for non-admin users:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin



