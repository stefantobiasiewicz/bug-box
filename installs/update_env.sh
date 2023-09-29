#!/bin/bash

# Configuration file path
config_file="/opt/bug-box/set-env.sh"
q
# Function to read and set a variable
set_variable() {
    current_value=$(grep "^export $1=" "$config_file" | cut -d'"' -f2)
    echo "Current value of $1 is: $current_value"
    echo -n "Enter a new value for $1: "
    read new_value
    # Set the variable in the configuration file
    sed -i "s/^export $1=.*/export $1=\"$new_value\"/" "$config_file"
    echo "Updated variable $1 to \"$new_value\"."
}

# Interactive menu
while true; do
    clear
    echo "1. Set BOX_NAME"
    echo "2. Set LED_PIXEL_COUNT"
    echo "3. Set IMAGE_CRON"
    echo "4. Set ENV_CRON"
    echo "5. Set BLOB_STORAGE_URL"
    echo "6. Set BLOB_STORAGE_ACCESS_KEY"
    echo "7. Set BLOB_STORAGE_SECRET_KEY"
    echo "8. Set BLOB_STORAGE_BUCKET"
    echo "9. Set MQTT_BROKER_URL"
    echo "10. Set MQTT_BROKER_PORT"
    echo "11. Set MQTT_BROKER_USERNAME"
    echo "12. Set MQTT_BROKER_PASSWORD"
    echo "13. Set MQTT_TOPIC"
    echo "0. Exit"

    read -p "Choose an option: " option
    case $option in
        1) set_variable "BOX_NAME";;
        2) set_variable "LED_PIXEL_COUNT";;
        3) set_variable "IMAGE_CRON";;
        4) set_variable "ENV_CRON";;
        5) set_variable "BLOB_STORAGE_URL";;
        6) set_variable "BLOB_STORAGE_ACCESS_KEY";;
        7) set_variable "BLOB_STORAGE_SECRET_KEY";;
        8) set_variable "BLOB_STORAGE_BUCKET";;
        9) set_variable "MQTT_BROKER_URL";;
        10) set_variable "MQTT_BROKER_PORT";;
        11) set_variable "MQTT_BROKER_USERNAME";;
        12) set_variable "MQTT_BROKER_PASSWORD";;
        13) set_variable "MQTT_TOPIC";;
        0) break;;
        *) echo "Invalid option";;
    esac
    read -p "Press Enter to continue..."
    read -p "Press Enter to continue..."
done
