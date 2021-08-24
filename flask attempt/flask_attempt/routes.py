import secrets
import os
from flask_attempt.ascii_thang import ascii_main
from PIL import Image
from flask import  render_template, url_for, flash, redirect, request, abort, send_file,send_from_directory
from flask_attempt.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, AsciiForm
from datetime import datetime
from flask_attempt.models import Post, User
from flask_attempt import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
use_x_sendfile = True
@app.route("/")
@app.route("/home")    #different routes for the website (home, about, etc.)
def home():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page = 5)
    return render_template('home.html', posts = posts) #returns the premade html templates which are stored in the directory

@app.route("/about")
def about():
    return render_template('about.html',title = "About")

@app.route("/register", methods = ['GET','POST'])
def register():
    if current_user.is_authenticated:       #if the user is logged in, redirect them to home page
        flash(f'You are already registered and logged in.', 'info')
        return redirect(url_for('home'))

    form = RegistrationForm()                 #gets the registration form made in forms.py
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')               #hashes the password
        user = User(username = form.username.data, email = form.email.data, password = hashed_pw)   #creates the user with values entered
        db.session.add(user)                                                                        #adds user to database
        db.session.commit()
        flash(f'Your account has been created! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html',title = "Register", form=form)

@app.route("/login", methods = ['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash(f'You are already logged in.', 'info')
        return redirect(url_for('home'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()  #finds user with the email entered in the form
        if user and bcrypt.check_password_hash(user.password, form.password.data):  #if the user entered in the form and the user attatched
            next_page = request.args.get('next') #used for redirecting after login  #with the hashed password match, the user is logged in
            login_user(user, remember = form.remember.data)
            return redirect(next_page) if next_page else redirect(url_for('home'))
            
        else:
            flash(f'Login unsuccessful. Please check email and/or password.', 'danger')
            
    return render_template('login.html',title = "Log In", form=form)
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture,type): #creates a special file name for each profile picture
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    if type == 'pfp':
        picture_path = os.path.join(app.root_path,'static/profile_pics/', picture_fn)  #saves it to big folder
        new_size = (125,125)
        pic = Image.open(form_picture)
        pic.thumbnail(new_size)
    elif type == 'ascii':
        picture_path = os.path.join(app.root_path,'static/ascii_pics/', picture_fn)  #saves it to big folder
        pic = Image.open(form_picture)
        pic.save(picture_path)
        return picture_path
    pic.save(picture_path)
    return picture_fn

@app.route("/account", methods = ['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data,'pfp')   #saves the image file
            current_user.image_file = picture_file          #uploads it to the users image box thing

        current_user.username = form.username.data              
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated','success')
        return redirect(url_for('account')) 
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename = 'profile_pics/' + current_user.image_file)
    return render_template('account.html', title = "Account", image_file = image_file, form = form)

@app.route("/post/new", methods = ['GET','POST'])
@login_required
def newpost():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title = form.title.data, content = form.content.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been submitted!', 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', title = "New Post", form = form, legend = 'New Post')
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html',title = post.title, post = post)

@app.route("/post/<int:post_id>/edit", methods = ['GET','POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id = post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title = "Update Post", form = form, legend = 'Update Post')

@app.route("/post/<int:post_id>/delete", methods = ['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!','info')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")    #different routes for the website (home, about, etc.)
def user_posts(username):
    page = request.args.get('page',1,type=int)
    user= User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(per_page = 5)
    return render_template('user_posts.html', posts=posts,user = user) #returns the premade html templates which are stored in the directory

@app.route("/ascii", methods = ['GET','POST'])
def jpeg_ascii():
    form = AsciiForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data,'ascii')   #saves the image file
            #image_file = url_for('static', filename = 'ascii_pics/' + picture_file)
            ascii_main(picture_file)
            os.remove(picture_file)
            uploads = os.path.join(app.root_path, 'Uploads/')
            send_from_directory(directory=uploads, filename='TextFile.txt', as_attachment = True)
    return render_template('ascii.html', form = form)

