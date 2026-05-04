# Anti Gravity Decor Store

**"Defy Gravity, Decorate in Pink Elegance"**

A fully-featured, premium e-commerce website built for a futuristic decor brand. The application lets users browse anti-gravity themed products, maintain their own private or guest shopping carts, and successfully check out with a complete order-tracking timeline feature. It is built to be completely bug-free with a resilient architecture that properly handles database resets and session sanitization.

## 🚀 Tech Stack Used

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite with Flask-SQLAlchemy (ORM)
- **Security & Authentication:** Werkzeug Security (password hashing), Flask Sessions
- **Template Engine:** Jinja2
- **Frontend Styling:** Pure HTML5 & Vanilla CSS3 
  - Implementation of a custom Glassmorphism UI
  - CSS Grid/Flexbox layouts with responsive design (Mobile, Tablet, Desktop)
  - Animated interactions (Lift effects, Hover glows, Image zoom)
- **Production Server:** Gunicorn (Deployment ready)

## ⭐ Core Features

1. **Robust Authentication**: Secure session-based login/register flows. Passwords hashed safely. Stale cookies automatically wiped on DB resets to avoid server crashes.
2. **Product & Order Management**: Custom models for `Product`, `Order`, `OrderItem`. Supports beautiful static product image rendering, precise low-stock warnings, and dynamic inventory math.
3. **Cart System**: Built to never crash. Uses temporary dictionary mappings if users are guests. Merges guest carts seamlessly into logged-in accounts on successful login.
4. **Checkout & Timelines**: Full checkout form with database constraints. Dynamic visual timeline tracing `Pending -> Confirmed -> Packed -> Shipped -> Delivered`.
5. **Modern Glassmorphism Aesthetic**: Beautiful, responsive pink/white futuristic decor styling with sleek modern UI.

---

## 💻 Local Setup Instructions

1. **Navigate to the core directory:**
   ```bash
   cd aviproject
   ```
2. **Setup a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Seed the database (Wipes any existing SQLite database & populates initial demo stock):**
   ```bash
   python seed.py
   ```
5. **Run the local Development Server:**
   ```bash
   python app.py
   ```
   *Visit `http://127.0.0.1:5000` in your web browser!*

---

## ☁️ AWS Deployment Guide (EC2 - Linux Ubuntu)

Once you are ready to put this online for real users, here is the robust way to deploy it on an AWS EC2 instance.

### 1) Launch your AWS EC2 Instance
- Go to AWS Console -> EC2 -> Launch Instance.
- Select **Ubuntu Server 22.04 LTS**.
- Add an existing or new **Security Group**. Ensure that **inbound ports 22 (SSH) and 80 (HTTP)** are open.

### 2) SSH into your Server & Prepare Requirements
```bash
ssh -i "your-key.pem" ubuntu@<your-ec2-ip>

sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx -y
```

### 3) Upload Project Files
You can clone this directory down from a private GitHub repo, or upload using `scp`. Make sure the `aviproject/` folder is placed on the server (e.g. `/home/ubuntu/aviproject`).

### 4) Environment Setup
```bash
cd /home/ubuntu/aviproject
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5) Run with Gunicorn (Background Service)
We use `gunicorn` instead of `app.run()` to safely handle production web traffic.
Let's create a *systemd* service file so the app spins up automatically if the server reboots!

Create the config file:
```bash
sudo nano /etc/systemd/system/aviproject.service
```
Paste the following inside it:
```ini
[Unit]
Description=Gunicorn daemon for Anti Gravity Store
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/aviproject
Environment="PATH=/home/ubuntu/aviproject/venv/bin"
ExecStart=/home/ubuntu/aviproject/venv/bin/gunicorn --workers 3 --bind unix:aviproject.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```
Start and enable the service:
```bash
sudo systemctl start aviproject
sudo systemctl enable aviproject
```

### 6) Configure Nginx (Reverse Proxy)
Nginx will filter out external web traffic into the Gunicorn worker.
```bash
sudo nano /etc/nginx/sites-available/aviproject
```
Add the following config (Replace server_name with your actual public EC2 IP or your domain):
```nginx
server {
    listen 80;
    server_name YOUR_PUBLIC_IP_OR_DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/aviproject/aviproject.sock;
    }

    # Better handling for static CSS & images avoiding Flask overhead
    location /static {
        alias /home/ubuntu/aviproject/static;
    }
}
```
Link and restart Nginx!
```bash
sudo ln -s /etc/nginx/sites-available/aviproject /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### Success!
Navigate to your Public EC2 IPv4 address on any browser securely. Your Anti Gravity Decor store is live!
