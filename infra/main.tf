resource "google_compute_network" "vpc_network" {
  name = "heritage-vpc"
}

resource "google_compute_subnetwork" "private_subnet" {
  name          = "private-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow_http" {
  name    = "allow-http"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["heritage-lens-backend"]
}

resource "google_compute_instance_template" "heritage_template" {
  name           = "heritage-lens-template-${var.redeploy_version}"
  machine_type   = var.vm_machine_type
  region         = var.region
  tags           = ["heritage-lens-backend"]

  disk {
    auto_delete  = true
    boot         = true
    source_image = var.vm_image
    disk_size_gb = 30
  }

  network_interface {
    network    = google_compute_network.vpc_network.id
    subnetwork = google_compute_subnetwork.private_subnet.id
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e

    apt-get update
    apt-get install -y git python3-venv nginx

    mkdir -p /opt/heritage-lens
    cd /opt/heritage-lens

    # Clone or update your repo
    if [ ! -d .git ]; then
      git clone https://github.com/mayurpawar/heritage-lens.git .
    else
      git pull
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "MONGO_URI=${var.mongo_uri}" > .env

    # Streamlit secrets for API_URL
    mkdir -p /opt/heritage-lens/.streamlit
    cat >/opt/heritage-lens/.streamlit/secrets.toml <<EOF
API_URL = "${var.frontend_api_url}"
EOF

    # FASTAPI SYSTEMD SERVICE
    cat >/etc/systemd/system/heritage-lens.service <<EOF
[Unit]
Description=Heritage Lens FastAPI backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/heritage-lens
EnvironmentFile=/opt/heritage-lens/.env
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/heritage-lens/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # STREAMLIT UI SYSTEMD SERVICE
    cat >/etc/systemd/system/heritage-lens-ui.service <<EOF
[Unit]
Description=Heritage Lens Streamlit UI
After=network.target

[Service]
User=root
WorkingDirectory=/opt/heritage-lens
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/heritage-lens/venv/bin/streamlit run app/ui/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # NGINX PROXY CONFIGURATION
    cat >/etc/nginx/sites-available/heritage-lens <<NGINX_CONF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # --- WebSocket support ---
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_CONF

    ln -sf /etc/nginx/sites-available/heritage-lens /etc/nginx/sites-enabled/heritage-lens
    rm -f /etc/nginx/sites-enabled/default
    systemctl restart nginx

    systemctl daemon-reload
    systemctl enable heritage-lens.service
    systemctl enable heritage-lens-ui.service
    systemctl restart heritage-lens.service
    systemctl restart heritage-lens-ui.service
  EOT

  metadata = {
    MONGO_URI           = var.mongo_uri
    FRONTEND_API_URL    = var.frontend_api_url
  }
}

resource "google_compute_region_instance_group_manager" "heritage_group" {
  name                = "heritage-lens-group"
  region              = var.region
  version {
    instance_template = google_compute_instance_template.heritage_template.id
  }
  base_instance_name  = "heritage-lens"
  target_size         = 1
  # Uncomment for autoscaling:
  # auto_healing_policies {
  #   health_check      = google_compute_health_check.default.self_link
  #   initial_delay_sec = 300
  # }
  lifecycle {
    create_before_destroy = true
  }
}

# Optionally add a health check for true production-grade
# resource "google_compute_health_check" "default" {
#   name               = "heritage-http-health"
#   http_health_check {
#     port             = 80
#     request_path     = "/"
#   }
# }

