# Yeelight to MQTT bridge

Works with Yeelight WiFi bulbs (color and monochrome).
You need to edit you bulb IPs in main.py (not yet fixed).

Sample docker-compose.yml file:
```
yeelight:
  build: .
  container_name: yeelight
  environment:
    - MQTT_SERVER=192.168.1.93
    - MQTT_USER=mqtt_user
    - MQTT_PASS=passw0rd
  restart: always
```

```
docker-compose build && docker-compose up -d
```

## Known bugs:
- Lamp's alive status updated only at startup.
- IP-Name list in main.py
- Bad code style =(