import os
import requests
import shutil
import time
import telebot
from telebot import types
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN", "7431504934:AAGLU6yBYp1dlVq05PWunh7yTiR2TdwMUWM")
bot = telebot.TeleBot(BOT_TOKEN)


def health_check():
    while True:
        try:
            r = requests.get("http://luna.pylex.xyz:11067", timeout=5)
            print(f"✅ Health check success: {r.status_code}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        time.sleep(100)


def download_and_upload(chat_id, urls, caption=""):
    caption = caption[:1024]
    media_files = []

    
    for i, url in enumerate(urls):
        try:
            r = requests.get(url, stream=True, timeout=20)
            content_type = r.headers.get("content-type", "")
            ext = "jpg" if "image" in content_type else "mp4"
            file_path = f"media_{i}.{ext}"
            with open(file_path, 'wb') as out_file:
                shutil.copyfileobj(r.raw, out_file)
            media_files.append((file_path, "photo" if "image" in content_type else "video"))
        except Exception as e:
            print("❌ Download error:", e)

    try:
        if len(media_files) == 1:
            fpath, ftype = media_files[0]
            if ftype == "photo":
                bot.send_photo(chat_id, photo=open(fpath, 'rb'), caption=caption)
            else:
                bot.send_video(chat_id, video=open(fpath, 'rb'), caption=caption)
        elif len(media_files) > 1:
            media_group = []
            for i, (fpath, ftype) in enumerate(media_files):
                if ftype == "photo":
                    media_group.append(types.InputMediaPhoto(open(fpath, 'rb'), caption=caption if i == 0 else None))
                else:
                    media_group.append(types.InputMediaVideo(open(fpath, 'rb'), caption=caption if i == 0 else None))
  
            for i in range(0, len(media_group), 10):
                bot.send_media_group(chat_id, media_group[i:i+10])
                time.sleep(3)
    except Exception as e:
        print("❌ Upload error:", e)
        bot.send_message(chat_id, "⚠️ Gagal mengupload media.")

    for f, _ in media_files:
        try:
            os.remove(f)
        except:
            pass

@bot.message_handler(commands=['ig', 'fb', 'tw', 'tt'])
def media_handler(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "⚠️ URL tidak valid. Silakan coba lagi.")

        command = parts[0].lower()
        url = parts[1]
        sent_msg = bot.reply_to(message, "⌛ Tunggu sebentar...")

        if command == "/ig":
            media = get_instagram_media(url)
        elif command == "/fb":
            media = get_facebook_video_url(url)
        elif command == "/tw":
            media = get_twitter_media(url)
        elif command == "/tt":
            media = get_tiktok_media(url)
        else:
            media = {"urls": [], "caption": ""}

        if media["urls"]:
            download_and_upload(message.chat.id, media["urls"], media.get("caption", ""))
            bot.delete_message(message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("❌ Tidak ada media yang ditemukan.", message.chat.id, sent_msg.message_id)

    except Exception as e:
        print("❌ Command Error:", e)
        bot.reply_to(message, "⚠️ Terjadi kesalahan, coba lagi nanti.")



def get_instagram_media(url):
    try:
        r = requests.get(
            "https://tikapi11-e3d106ab50c7.herokuapp.com/api",
            params={"url": url},
            headers={
                "Host": "tikapi11-e3d106ab50c7.herokuapp.com",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36 Telegram-Android/11.12.0.0 (Xiaomi 23116PN5BC; Android 10; SDK 29; HIGH)",
                "Accept": "*/*",
                "X-Requested-With": "org.telegram.plus",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://tikapi11-e3d106ab50c7.herokuapp.com/downloader",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "id,id-ID;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        print(r.text)

        if r.status_code == 200:
            data = r.json()
            if "data" in data:
                content = data["data"]
                caption = content.get("caption", "Tidak ada caption")
                urls = content.get("url", [])
                count = content.get("media_count", len(urls))
                return {"urls": urls, "caption": caption, "count": count}
    except Exception as e:
        print("❌ Instagram Error:", e)

    return {"urls": [], "caption": "Tidak ada caption", "count": 0}

def get_twitter_media(url):
    try:
        r = requests.get("https://twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com/status",
                         headers={
                             "x-rapidapi-key": "4f281a1be0msh5baa41ebeeda439p1d1139jsn3c26d05da8dd",
                             "x-rapidapi-host": "twitter-downloader-download-twitter-videos-gifs-and-images.p.rapidapi.com"
                         },
                         params={"url": url})
        if r.status_code == 200:
            data = r.json()
            video = data.get("media", {}).get("video", {}).get("videoVariants", [])
            if video:
                return {"urls": [video[0]["url"]]}
    except Exception as e:
        print("❌ Twitter Error:", e)
    return {"urls": []}


def get_tiktok_media(url):
    try:
        r = requests.get(f"https://www.tikwm.com/api/?url={url}")
        if r.status_code == 200:
            data = r.json().get("data", {})
            if data.get("play") and not data["play"].endswith(".mp3"):
                return {"urls": [data["play"]], "caption": data.get("title", "Tidak ada caption.")}
            if isinstance(data.get("images"), list) and data["images"]:
                return {"urls": data["images"], "caption": data.get("title", "Tidak ada caption.")}
    except Exception as e:
        print("❌ TikTok Error:", e)
    return {"urls": []}


def get_facebook_video_url(fb_url):
    url = f"https://vdfr.aculix.net/fb?url={fb_url}"
    headers = {"Authorization": "erg4t5hyj6u75u64y5ht4gf3er4gt5hy6uj7k8l9"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            media = data.get("media", [])
            for item in media:
                if item.get("is_video"):
                    return {"urls": [item.get("video_url")]}
    except Exception as e:
        print("❌ Facebook Error:", e)
    return {"urls": []}


@bot.message_handler(commands=["cc"])
def capcut_handler(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            return bot.reply_to(message, "⚠️ Masukkan link CapCut!")

        link = parts[1]
        sent_msg = bot.reply_to(message, "⏳ Mengambil video...")

        url = "https://3bic.com/api/download"
        headers = {
            "authority": "3bic.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://3bic.com",
            "referer": "https://3bic.com/",
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
        }
        data = {"url": link}

        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()

        original_video_path = res_json.get("originalVideoUrl", "")
        full_video_url = f"https://3bic.com{original_video_path}"
        cover = res_json.get("coverUrl")
        title = res_json.get("title", "Tanpa judul")
        urls = [cover, full_video_url]
        download_and_upload(message.chat.id, urls, title)
        bot.delete_message(message.chat.id, sent_msg.message_id)

    except Exception as e:
        print("❌ CapCut Error:", e)
        bot.reply_to(message, "⚠️ Terjadi kesalahan saat memproses link CapCut.")


if __name__ == "__main__":
    Thread(target=health_check).start()
    print("Bot started...")
    bot.infinity_polling()
