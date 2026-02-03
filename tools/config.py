import os

# Invoice Ninja API Configuration
NINJA_URL = os.getenv("NINJA_URL")
NINJA_TOKEN = os.getenv("NINJA_TOKEN")

# Standard headers required by Invoice Ninja v5
HEADERS = {
    "X-Api-Token": NINJA_TOKEN,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json"
}
