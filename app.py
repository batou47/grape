import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application
app = Flask(__name__)

# Custom filter

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///shop.db")





@app.route("/", methods=["GET"])
def default():
    return redirect("/catalog")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
           # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", message="Invalid username/password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Check if there's a redirect URL in the session
        redirect_url = session.get("redirect_url")
        if redirect_url:
            # Clear the stored URL before redirecting
            session.pop("redirect_url", None)
            return redirect(redirect_url)

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # If submitted via post
    if request.method == "POST":
        # Get user's input
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", email)
        if len(rows) != 0:
            return render_template("error.html", message="E-mail adress already in use")

        # Insert user's details into users database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", email, generate_password_hash(password))

        # Get user's id
        rows = db.execute("SELECT * FROM users WHERE username = ?", email)
        session["user_id"] = rows[0]["id"]

        return redirect("/login")

    # If submitted via get, simply render register template
    else:
        return render_template("register.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        db.execute("INSERT INTO contact (name, email, subject, message) VALUES (?, ?, ?, ?)", name, email, subject, message)
        return redirect("/")

    else:
        return render_template("contact.html")




@app.route("/catalog", methods=["GET"])
def catalog():
    dunks= db.execute("SELECT * FROM products WHERE collection = 'dunk low'")
    j1_highs = db.execute("SELECT * FROM products WHERE collection = 'jordan 1 high'")
    j1_lows = db.execute("SELECT * FROM products WHERE collection = 'jordan 1 low'")
    j4s = db.execute("SELECT * FROM products WHERE collection = 'jordan 4'")

    user_logged_in = session.get("user_id") is not None  # Check if user is logged in
    return render_template("catalog.html", dunks=dunks, j1_highs=j1_highs, j1_lows=j1_lows, j4s=j4s, user_logged_in=user_logged_in)


@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_page(product_id):
    product = db.execute("SELECT * FROM products WHERE id = ?", product_id)
    product = product[0]


    if request.method == "POST":
        size = request.form.get("size")
        quantity = request.form.get("quantity")
        if "user_id" not in session:
            return redirect("/login")

        if not size:
            return render_template("error.html", message="Must Select Size")

        db.execute("INSERT INTO cart (user_id, product_id, brand, collection, model, price, image, color, description, year, additional_info, size, quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   session["user_id"], product["id"], product["brand"], product["collection"], product["model"], product["price"], product["image"], product["color"], product["description"],
                   product["year"], product["additional_info"], size, quantity)
        return redirect('/catalog')

    else:
        user_logged_in = session.get("user_id") is not None  # Check if user is logged in
        return render_template('product.html', product=product, user_logged_in=user_logged_in)


@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("home.html")



@app.route("/cart", methods=["GET", "POST"])
def cart():

    if "user_id" not in session:
            return redirect("/login")

    user_logged_in = session.get("user_id") is not None  # Check if user is logged in

    products = db.execute("SELECT * FROM cart WHERE user_id = ?", session["user_id"])

    count = 0
    subtotal = 0
    for product in products:
        count += product["quantity"]
        price = product["price"].replace(",", "")
        subtotal += float(price) * product["quantity"]

    shipping = 5.0
    total = subtotal + shipping
    subtotal = ('{:,}'.format(subtotal))
    total = ('{:,}'.format(total))

    return render_template("cart.html", user_logged_in=user_logged_in, products=products, count=count, subtotal=subtotal, total=total, shipping=shipping)


@app.route("/remove/<int:product_id>/<size>", methods=["GET", "POST"])
def remove(product_id, size):

    # Get the product_id from the query parameter
    product_id = product_id

    # Get the size from the query parameter
    size = size

    # Delete the product from the cart
    db.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ? AND size = ?", session["user_id"], product_id, size)

    return redirect('/cart')