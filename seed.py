from app import app
from models import db, Product, User
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # WARNING: This wipes existing data to apply the new schema
        db.drop_all()
        db.create_all()
        
        # 1. Seed Users
        admin_pw = generate_password_hash("admin123")
        admin = User(full_name="System Admin", email="admin@aviproject.local", password_hash=admin_pw)
        
        test_pw = generate_password_hash("test1234")
        test_user = User(full_name="Test Customer", email="test@user.local", password_hash=test_pw, address="123 Nebula Way", city="Star City", pincode="12345")
        
        db.session.add(admin)
        db.session.add(test_user)
        
        # 2. Seed Products
        products = [
            Product(
                name="Levitating Magnetic Plant Pod",
                description="A beautiful spinning geometric planter that hovers gracefully above its oak base. Perfect for air plants or small succulents.",
                price=3499.00,
                stock=15,
                image_url="/static/css/images/products/Levitating Magnetic Plant Pod.jpg"
            ),
            Product(
                name="Anti-Gravity Floating Moon Lamp",
                description="Experience the magic of the moon in your room. This 3D printed lunar replica floats and slowly rotates just like the real thing.",
                price=5200.00,
                stock=8,
                image_url="/static/css/images/products/Anti-Gravity Floating Moon Lamp.jpg"
            ),
            Product(
                name="Zero-G Coffee Cup",
                description="An optical illusion mug that appears to float above the table. Comes with a matching magnetic coaster.",
                price=1299.50,
                stock=25,
                image_url="/static/css/images/products/Zero-G Coffee Cup.webp"
            ),
            Product(
                name="Hovering Bluetooth Speaker",
                description="Crystal clear 360-degree sound from a futuristic pink orb that magnetically levitates over a futuristic base.",
                price=4500.00,
                stock=10,
                image_url="/static/css/images/products/Hovering Bluetooth Speaker.webp"
            ),
            Product(
                name="Magnetic Floating Globe",
                description="An educational and mesmerizing piece for your desk. The world map floats dynamically through magnetic induction.",
                price=2100.00,
                stock=20,
                image_url="/static/css/images/products/Magnetic Floating Globe.webp"
            ),
            Product(
                name="Defying Gravity Bookshelf",
                description="A concealed shelf that makes your books look like they are floating against the wall magically in mid-air.",
                price=850.00,
                stock=40,
                image_url="/static/css/images/products/Defying Gravity Bookshelf.jpg"
            ),
            Product(
                name="Floating Light Bulb",
                description="Vintage Edison style light bulb that floats and illuminates wirelessly. An absolute conversation starter.",
                price=6500.00,
                stock=5,
                image_url="/static/css/images/products/Floating Light Bulb.webp"
            ),
            Product(
                name="Kinetic Orbit Sculpture",
                description="A mesmerizing desktop toy that uses magnets to create near-perpetual motion, simulating planetary orbits.",
                price=1800.00,
                stock=30,
                image_url="/static/css/images/products/Kinetic Orbit Sculpture.webp"
            )
        ]
        
        db.session.bulk_save_objects(products)
        db.session.commit()
        print("Database wiped & successfully seeded with Users and Products!")

if __name__ == '__main__':
    seed_data()
