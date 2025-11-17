from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
#from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "minha_chave"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = "login"
#CORS(app)


class carrinho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)

class usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship("carrinho", backref="usuario", lazy=True)

class produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return usuario.query.get(int(user_id))

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = usuario.query.filter_by(username=data.get("username")).first()
    if user and data.get("password") == user.password:
            login_user(user)
            return jsonify({"message": "Logged in successfully"})
    return  jsonify({"message": "unauthorized"}), 401

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successfully"})

@app.route("/api/products/add", methods=["POST"])
@login_required
def add_product():
    data = request.json
    if "name" in data and "price" in data:
        product = produto(name=data.get("name", ""),price=data.get("price", ""),description=data.get("description", ""))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "PRODUCT ADDED SUCCESSFULLY"})
    return jsonify({"message": "INVALID PRODUCT DATA"}), 400

@app.route("/api/products/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = produto.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "DELETE SUCCESSFULLY"})
    return jsonify({"message": "Product not found"}), 404

@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product_details(product_id):
    product = produto.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        })
    return jsonify({"message": "product not found"}), 404

@app.route("/api/products/update/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    product = produto.query.get(product_id)
    if not product:
        return jsonify({"message": "product not found"}), 404
    
    data = request.json
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = data["price"]
    if "description" in data:
        product.description = data["description"]
    db.session.commit()
    return jsonify({"message": "product update successfully"})

@app.route("/api/products", methods=["GET"])
def get_products():
    products = produto.query.all()
    product_list = []
    for i in products:
        product_data = {
            "id": i.id,
            "name": i.name,
            "price": i.price
        }
        product_list.append(product_data)
    return jsonify(product_list)
    
@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    user = usuario.query.get(int(current_user.id))
    product = produto.query.get(product_id)
    if user and product:
        cart_item = carrinho(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({"message": "Item added to cart!"})
    return jsonify ({"message": "Failed to added item to the cart!"}), 400

@app.route("/api/cart/remove/<int:product_id>", methods=["DELETE"])
@login_required
def remove_cart(product_id):
    cart_item = carrinho.query.filter_by(user_id=current_user.id,product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "item removed successfully"})
    return jsonify({"message": "failed to remove item from cart"}), 400

@app.route("/api/cart", methods=["GET"])
@login_required
def view_cart():
    user = usuario.query.get(current_user.id)
    cart_items = user.cart
    cart_list = []
    for i in cart_items:
        product = produto.query.get(i.product_id)
        cart_list.append({
            "id": i.id,
            "user_id": i.user_id,
            "prduct_id": i.product_id,
            "product_name": product.name,
            "product_price": product.price,
        })
    return jsonify(cart_list)

@app.route("/api/cart/checkout/", methods=["POST"])
@login_required
def checkout():
    user = usuario.query.get(current_user.id)
    cart_items = user.cart
    for i in cart_items:
        db.session.delete(i)
    db.session.commit()
    return jsonify({"message": "checkout successfully"})


if __name__ == "__main__":
    app.run (debug=True)