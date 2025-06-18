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

resource "google_service_account" "vm_sa" {
  account_id   = "${var.project_name}-vm-sa"
  display_name = "Service Account for ${var.project_name} Instance Group"
}

resource "google_project_iam_member" "vm_sa_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
}

resource "google_project_iam_member" "vm_sa_vertexai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vm_sa.email}"
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

  service_account {
    email  = google_service_account.vm_sa.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e

    # Install Google Cloud SDK if not available (Debian/Ubuntu example)
    if ! command -v gcloud &> /dev/null
    then
      echo "Installing gcloud..."
      apt-get update && apt-get install -y apt-transport-https ca-certificates gnupg
      echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
      curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
      apt-get update && apt-get install -y google-cloud-sdk
    fi

    # Fetch secret from Secret Manager and export as env variable (example)
    export MONGO_URI=$(gcloud secrets versions access latest --secret="heritage_lens_mongo_uri" --project="${var.project_id_number}")
    export MONGO_DB_NAME=$(gcloud secrets versions access latest --secret="heritage_lens_mongo_dbname" --project="${var.project_id_number}")
    export MONGO_COLLECTION=$(gcloud secrets versions access latest --secret="heritage_lens_mongo_db_collection" --project="${var.project_id_number}")

    echo "MONGO_URI=$MONGO_URI" >> /etc/environment
    echo "MONGO_DB_NAME=$MONGO_DB_NAME" >> /etc/environment
    echo "MONGO_COLLECTION=$MONGO_COLLECTION" >> /etc/environment

    # Use $MONGO_URI in your application start command or pass it as needed
    
    apt-get update
    apt-get install -y git python3-venv nginx
    apt-get install -y certbot python3-certbot-nginx

    # Fetch cert, key, and config files from Secret Manager
    sudo mkdir -p /etc/letsencrypt/live/${var.domain}

    gcloud secrets versions access latest --secret="${var.secret_name_cert_fullchain}" --project="${var.project_id_number}" | sudo tee /etc/letsencrypt/live/${var.domain}/fullchain.pem > /dev/null
    gcloud secrets versions access latest --secret="${var.secret_name_cert_privatekey}" --project="${var.project_id_number}" | sudo tee /etc/letsencrypt/live/${var.domain}/privkey.pem > /dev/null
    sudo chmod 600 /etc/letsencrypt/live/${var.domain}/privkey.pem

    gcloud secrets versions access latest --secret="cert-options-ssl-nginx-conf" --project="${var.project_id_number}" | sudo tee /etc/letsencrypt/options-ssl-nginx.conf > /dev/null
    gcloud secrets versions access latest --secret="cert-ssl-dhparams-pem" --project="${var.project_id_number}" | sudo tee /etc/letsencrypt/ssl-dhparams.pem > /dev/null


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

    # Streamlit secrets for API_URL
    mkdir -p /opt/${var.project_name}/.streamlit
    cat >/opt/${var.project_name}/.streamlit/secrets.toml <<EOF
API_URL = "https://${var.domain}/api/explorer/search"
EOF

    # FASTAPI SYSTEMD SERVICE
    cat >/etc/systemd/system/${var.project_name}.service <<EOF
[Unit]
Description=Heritage Lens FastAPI backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/${var.project_name}
EnvironmentFile=/etc/environment
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
    cat >/etc/nginx/sites-available/${var.project_name} <<NGINX_CONF
server {
    server_name ${var.domain} www.${var.domain};

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # --- WebSocket support ---
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /assets/ {
        alias /opt/heritage-lens/app/ui/assets/;
        autoindex off;
    }
    listen 443 ssl; # managed by Certbot. Comment this section for firsttime setup.
    ssl_certificate /etc/letsencrypt/live/${var.domain}/fullchain.pem; # managed by Certbot. Comment this section for firsttime setup.
    ssl_certificate_key /etc/letsencrypt/live/${var.domain}/privkey.pem; # managed by Certbot. Comment this section for firsttime setup.
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot. Comment this section for firsttime setup.
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot. Comment this section for firsttime setup.

}
server {
    if (\$host = ${var.domain}) {
        return 301 https://\$host\$request_uri;
    } # managed by Certbot


    listen 80;
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
    BACKEND_API_URL    = "https://${var.domain}/api/explorer/search"
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
  target_size         = 2
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
