# Rover1/ministries/camera/config.py

HOST = "2.tcp.ngrok.io"      # or whatever ngrok endpoint maps to camera host
PORT = 18252                 # camera listener on host

RESOLUTION = (640, 480)
QUALITY = 80
FPS = 10

HEALTH_INTERVAL = 5
CONNECT_RETRY_DELAY = 5
