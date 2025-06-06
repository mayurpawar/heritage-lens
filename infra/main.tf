resource "google_compute_network" "vpc_network" {
  name = "${var.project_name}-vpc"
}

resource "google_compute_subnetwork" "private_subnet" {
  name          = "${var.project_name}-private-subnet"
  ip_cidr_range = var.cidr_range
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.project_name}-allow-ssh"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow_http" {
  name    = "${var.project_name}-allow-http"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-backend"]
}

resource "google_compute_firewall" "allow_https" {
  name    = "${var.project_name}-allow-https"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.project_name}-backend"]
}

resource "google_compute_instance_template" "heritage_template" {
  name           = "${var.project_name}-template-${var.redeploy_version}"
  machine_type   = var.vm_machine_type
  region         = var.region
  tags           = ["${var.project_name}-backend"]

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
    apt-get install -y certbot python3-certbot-nginx

    mkdir -p /opt/${var.project_name}
    cd /opt/${var.project_name}

    # Clone or update your repo
    if [ ! -d .git ]; then
      git clone https://github.com/mayurpawar/${var.project_name}.git .
    else
      git pull
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "MONGO_URI=${var.mongo_uri}" > .env

    # Streamlit secrets for API_URL
    mkdir -p /opt/${var.project_name}/.streamlit
    cat >/opt/${var.project_name}/.streamlit/secrets.toml <<EOF
API_URL = "${var.frontend_api_url}"
EOF

    # FASTAPI SYSTEMD SERVICE
    cat >/etc/systemd/system/${var.project_name}.service <<EOF
[Unit]
Description=Heritage Lens FastAPI backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/${var.project_name}
EnvironmentFile=/opt/${var.project_name}/.env
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/${var.project_name}/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # STREAMLIT UI SYSTEMD SERVICE
    cat >/etc/systemd/system/${var.project_name}-ui.service <<EOF
[Unit]
Description=Heritage Lens Streamlit UI
After=network.target

[Service]
User=root
WorkingDirectory=/opt/${var.project_name}
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/${var.project_name}/venv/bin/streamlit run app/ui/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # NGINX PROXY CONFIGURATION (disable variable expansion!)
    cat >/etc/nginx/sites-available/${var.project_name} <<"NGINX_CONF"
server {
    listen 80;
    server_name heritage.mayurpawar.com www.heritage.mayurpawar.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # --- WebSocket support ---
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONF

    ln -sf /etc/nginx/sites-available/${var.project_name} /etc/nginx/sites-enabled/${var.project_name}
    rm -f /etc/nginx/sites-enabled/default
    systemctl restart nginx

    systemctl daemon-reload
    systemctl enable ${var.project_name}.service
    systemctl enable ${var.project_name}-ui.service
    systemctl restart ${var.project_name}.service
    systemctl restart ${var.project_name}-ui.service
  EOT

  metadata = {
    MONGO_URI           = var.mongo_uri
    FRONTEND_API_URL    = var.frontend_api_url
  }
}

resource "google_compute_region_instance_group_manager" "heritage_group" {
  name                       = "${var.project_name}-template-${var.redeploy_version}"
  region                     = var.region
  distribution_policy_zones  = ["${var.zone}"]
  version {
    instance_template = google_compute_instance_template.heritage_template.id
  }
  base_instance_name  = "${var.project_name}"
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
