#!/bin/bash

set -e

echo "Installing Redis server..."
sudo apt update
sudo apt install -y redis-server

echo "Configuring Redis..."
sudo sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf
sudo sed -i 's/^# requirepass .*/requirepass redis123/' /etc/redis/redis.conf
sudo sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf

echo "Restarting Redis service..."
sudo systemctl enable redis-server
sudo systemctl restart redis-server

echo ""
echo "Redis installed successfully!"
echo "=========================="
echo "Password: redis123"
echo "Local access: 127.0.0.1:6379"
echo "Network access (192.168.122.x): $(ip addr show | grep 'inet 192.168.122' | awk '{print $2}' | cut -d/ -f1):6379"
echo ""
echo "Test connection: redis-cli -a redis123 ping"
