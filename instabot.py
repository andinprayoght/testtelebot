import os
import requests
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo

# Konfigurasi bot
BOT_TOKEN = "7431504934:AAGLU6yBYp1dlVq05PWunh7yTiR2TdwMUWM"
APP_ID = 961780
API_HASH = "bbbfa43f067e1e8e2fb41f334d32a6a7"
bot = Client("social_downloader", bot_token=BOT_TOKEN, api_id=APP_ID, api_hash=API_HASH)

def download_and_upload(client, message, media_urls, caption=""):
    media_files = []
    
    caption = caption[:1024]  # Batasan caption Telegram

    for media_url in media_urls:
        head_response = requests.head(media_url)
        content_type = head_response.headers.get("Content-Type", "")
        file_ext = "mp4" if "video" in content_type else "jpg"
        file_path = f"media_{len(media_files) + 1}.{file_ext}"
        
        response = requests.get(media_url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            media_files.append(file_path)

    if len(media_files) == 1:
        file = media_files[0]
        if file.endswith(".mp4"):
            client.send_video(message.chat.id, video=file, caption=caption)
        else:
            client.send_photo(message.chat.id, photo=file, caption=caption)
    else:
        batch_size = 10
        for i in range(0, len(media_files), batch_size):
            media_group = []
            for idx, file in enumerate(media_files[i:i + batch_size]):
                if file.endswith(".mp4"):
                    media = InputMediaVideo(file, caption=caption if idx == 0 else "")
                else:
                    media = InputMediaPhoto(file, caption=caption if idx == 0 else "")
                media_group.append(media)
            client.send_media_group(message.chat.id, media_group)

    for file in media_files:
        os.remove(file)

@bot.on_message(filters.command(["ig", "fb", "tw", "tt"]))
def handle_command(client, message: Message):
    try:
        command, url = message.text.split(" ", 1)
    except ValueError:
        message.reply("⚠️ URL tidak valid. Silakan coba lagi.")
        return

    message.reply("⌛ Tunggu sebentar...")

    if command == "/ig":
        media_data = get_instagram_media(url)
        if media_data:
            media_urls = media_data["urls"]
            caption = media_data.get("caption", "").strip().replace("\\n", "\n")
            download_and_upload(client, message, media_urls, caption)
        else:
            message.reply("❌ Tidak ada media yang ditemukan.")

def generate_fake_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0",
        "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL Build/QD1A.190805.021) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    ]
    accept_languages = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7", "de;q=0.6", "fr;q=0.5"]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": random.choice(accept_languages),
        "Cache-Control": "no-cache",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
    }

def get_instagram_media(instagram_url):
    api_url = "https://api.snapx.info/v1/instagram"
    headers = generate_fake_headers()
    headers.update({
        "content-type": "application/json",
        "accept": "application/json",
        "x-app-id": "24340030",
        "x-app-token": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOiIxNzI2NzgwODQwNzExIn0.5M65C_Rz_C3H4mkIQ3WvgfrpqD6lJmeDc-CK3x_Lbfw",
    })

    response = requests.get(api_url, headers=headers, params={"url": instagram_url})

    if response.status_code == 200:
        try:
            data = response.json().get("data", {})

            images, videos = [], []
            caption = data.get("title", "Tidak ada caption.")

            if data.get("__type") == "GraphSidecar":
                for item in data.get("items", []):
                    if item.get("__type") == "GraphVideo" and item.get("video_url"):
                        videos.append(item["video_url"])
                    elif item.get("display_url"):
                        images.append(item["display_url"])

            elif data.get("__type") == "GraphVideo" and data.get("video_url"):
                videos.append(data["video_url"])

            elif data.get("display_url"):
                images.append(data["display_url"])

            media_urls = images + videos
            return {"urls": media_urls, "caption": caption}

        except Exception as e:
            print(f"Error parsing JSON response: {e}")

    return None

def get_facebook_video_url(fb_url):
    url = f"https://vdfr.aculix.net/fb?url={fb_url}"
    headers = {"Authorization": "erg4t5hyj6u75u64y5ht4gf3er4gt5hy6uj7k8l9"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        media = data.get("media", [])
        for item in media:
            if item.get("is_video"):
                return item.get("video_url")
    return None

def twitter_api(twitter_url):
    url = "https://twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com/status"
    headers = {
        "x-rapidapi-key": "4f281a1be0msh5baa41ebeeda439p1d1139jsn3c26d05da8dd",
        "x-rapidapi-host": "twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com",
    }
    response = requests.get(url, params={"url": twitter_url}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        variants = data.get("media", {}).get("video", {}).get("videoVariants", [])
        for variant in variants:
            if variant.get("content_type") == "video/mp4":
                return variant.get("url")
    return None

def get_tiktok_media(tiktok_url):
    url = f"https://www.tikwm.com/api/?url={tiktok_url}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if images := data.get("data", {}).get("images"):
            return {"type": "image", "urls": images}
        if play := data.get("data", {}).get("play"):
            return {"type": "video", "urls": [play]}
    return None

if __name__ == "__main__":
    bot.run()
