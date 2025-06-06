output "instance_group_manager" {
  value = google_compute_region_instance_group_manager.heritage_group.self_link
}

output "instance_template" {
  value = google_compute_instance_template.heritage_template.self_link
}

output "instance_ip" {
  value = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}