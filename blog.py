from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
            if "logged_in" in session:
                return f(*args, **kwargs)    
            else:
                flash("bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
                return redirect(url_for("login"))
    return decorated_function

class LoginForm(Form):
    username = StringField("kullanıcı adı")
    password = PasswordField("Parola:")

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25)])
    username = StringField("kullanıcı adı",validators=[validators.Length(min=5,max=35)])
    email = StringField("Email Adresi",validators=[validators.Email(message="lütfen geçerli bir email adresi giriniz.")])
    password = PasswordField("Parola:",validators=[validators.DataRequired(message="lütfen bir parola belirleyiniz."),validators.EqualTo(fieldname="confirm",message="parolanız uyuşmuyor.")])
    confirm = PasswordField("parola doğrula")
    
class ArticleForm(Form):
    title = StringField("makale başlığı",validators=[validators.Length(min = 5,max = 100)])
    content = TextAreaField("makale içeriği",validators=[validators.Length(min=10)])
app = Flask(__name__)
app.secret_key = "blog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/articles/<string:id>")
def detail(id):
    return "article id:"+id
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("başarıyla kayıt oldunuz.","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        enteredpassword = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            realpassword = data["password"]
            if sha256_crypt.verify(enteredpassword,realpassword):
                flash("başarıyla giriş yaptınız.","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("parolanızı yanlış girdiniz.","danger")
                return redirect(url_for("login"))
        else:
            flash("böyle bir kıllanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form=form)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",keyarticles = articles)
    else:
        return render_template("dashboard.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",keyarticles=articles)
    else:
        return render_template("articles.html")

@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("makaleniz başarıyla eklendi.","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))  
    if result > 0:
        sorgu2 = "Delete From articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("böyle bir makale yok veya böyle bir işleme yetkiniz yok.")
        return redirect(url_for("index"))
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where author = %s and id = %s"
        result = cursor.execute(sorgu,(session["username"],id))  
        if result > 0:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)
        else:
            flash("böyle bir makale yok veya böyle bir işleme yetkiniz yok.","danger")
            return redirect(url_for("index"))
    else:
        form = ArticleForm(request.form)
        newtitle=form.title.data
        newcontent=form.content.data
        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()
        flash("makale başarıyla güncellendi.","success")
        return redirect(url_for("dashboard"))
        


@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))   
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",keyarticle=article)
    else:
        return render_template("article.html")
    
    
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where title like '%" +keyword+ "%' "
        result = cursor.execute(sorgu)
        if result > 0:
            articles = cursor.fetchall()
            return render_template("articles.html",keyarticles=articles)
        else:
            flash("aranan kelimeye uygun makale bulunamadı.","warning")          
            return redirect(url_for("articles"))
if __name__=="__main__":
    app.run(debug=True)
