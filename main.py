# Import OS and DotEnv and DATETIME
import os
import dotenv
from functools import wraps
from datetime import date, datetime

# Flask App, Bootstrap and Gravatar for the front-end
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
# from flask_gravatar import Gravatar

# Flask SQLAlchemy, Login and Bcrypt for Authentication
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
from flask_bcrypt import Bcrypt

# Flask WTForms and CKEditor for Forms
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

dotenv.load_dotenv('.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
bootstrap = Bootstrap5(app=app)
# gravatar = Gravatar(app=app)
migrate = Migrate(app=app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_database.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app=app)

bcrypt = Bcrypt(app=app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# DB Models
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")


class Post(db.Model):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(100), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(db.Model):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    datetime: Mapped[str] = mapped_column(String(30), nullable=False)  # date.today().strftime("%B %d, %Y %I:%M:%S")
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("posts.id"))
    post = relationship("Post", back_populates="comments")


# Create Flask Forms
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    content = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Me Up')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Let Me In')


class CommentForm(FlaskForm):
    comment = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


with app.app_context():
    db.create_all()


# Create Routes
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
    result = db.session.execute(db.select(Post))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(Post, post_id)
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
        new_post = Post(
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
    post = db.get_or_404(Post, post_id)
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
    post_to_delete = db.get_or_404(Post, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=True)
