import datetime

from models import User, BlogPost, Comment

from datetime import date, datetime
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from functools import wraps
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm


def register_routes(app, db):
    # init LoginManager
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'

    # init Bcrypt
    bcrypt = Bcrypt(app)

    gravatar = Gravatar(app)

    def admin_only(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if current_user.id != 1:
                return abort(403)
            return func(*args, **kwargs)
        return decorated_function

    @login_manager.user_loader
    def load_user(user_id):
        return db.get_or_404(User, user_id)

    @app.context_processor
    def year_now():
        return {'year_now': datetime.now().year}

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            pw_hash = bcrypt.generate_password_hash(password=form.password.data, rounds=8)
            new_user = User(name=form.name.data, email=form.email.data, password=pw_hash)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('You\'ve signed up successfully!')
            return redirect(url_for('get_all_posts'))
        return render_template("register.html", form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
            print('Finding user')
            if user:
                print('user found')
                if bcrypt.check_password_hash(pw_hash=user.password, password=form.password.data):
                    print('password matched')
                    login_user(user)
                    print(current_user.name)
                    flash('You have been logged in!')
                    return redirect(url_for('get_all_posts'))
                else:
                    print('password did not match')
                    return redirect(url_for('login'))
            else:
                flash('Account not registered!')
                return redirect(url_for('login'))
        else:
            return render_template("login.html", form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out!')
        return redirect(url_for('get_all_posts'))

    @app.route('/')
    def get_all_posts():
        result = db.session.execute(db.select(BlogPost))
        posts = result.scalars().all()
        return render_template("index.html", all_posts=posts)

    @app.route("/post/<int:post_id>", methods=['GET', 'POST'])
    def show_post(post_id):
        requested_post = db.get_or_404(BlogPost, post_id)
        form = CommentForm()
        if form.validate_on_submit():
            new_comment = Comment(
                body=form.comment.data,
                datetime=datetime.now().strftime("%B %d, %Y %I:%M:%S"),
                user=current_user,
                post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
        else:
            return render_template("post.html", post=requested_post, form=form)

    @app.route("/new-post", methods=["GET", "POST"])
    @login_required
    def add_new_post():
        form = CreatePostForm()
        if form.validate_on_submit():
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form)

    @app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
    @login_required
    def edit_post(post_id):
        post = db.get_or_404(BlogPost, post_id)
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = current_user
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
        return render_template("make-post.html", form=edit_form, is_edit=True)

    @app.route("/delete/<int:post_id>")
    @login_required
    def delete_post(post_id):
        post_to_delete = db.get_or_404(BlogPost, post_id)
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('get_all_posts'))

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")
