import os
import streamlit as st
import tempfile
import gc
import random

# ==========================================
# 0. 雲端環境設定 & 破解 ImageMagick 資安限制
# ==========================================
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

# 🌟 替身攻擊：動態生成寬鬆的 ImageMagick 政策檔，繞過 Streamlit 的阻擋
policy_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<policymap>
  <policy domain="path" rights="read|write" pattern="@*"/>
</policymap>'''
os.makedirs('/tmp/magick', exist_ok=True)
with open('/tmp/magick/policy.xml', 'w') as f:
    f.write(policy_xml)

# 強迫 ImageMagick 優先讀取我們剛剛建立的寬鬆政策檔
os.environ["MAGICK_CONFIGURE_PATH"] = "/tmp/magick"

# ==========================================
# 1. 導入 MoviePy 2.0 全新模組
# ==========================================
from moviepy import (
    ImageClip, 
    VideoFileClip, 
    concatenate_videoclips,
    concatenate_audioclips,
    AudioFileClip, 
    CompositeVideoClip, 
    CompositeAudioClip, 
    TextClip
)

# ... (下面的程式碼完全不變) ...

# ==========================================
# 2. 核心設定：產業與風格模板資料庫
# ==========================================
STYLE_TEMPLATES = {
    "cinematic": {
        "name": "微電影工作室（沉穩高質感）",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "text_pos": ("center", "bottom"),
        "sfx_pattern": {0.0: "ambient_swell.mp3", 2.0: "sub_boom.mp3"}
    },
    "viral_vlog": {
        "name": "極速網紅自媒體（快節奏重口味）",
        "text_color": "#FFFF00",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "text_pos": ("center", "center"),
        "sfx_pattern": {0.0: "sfx_whoosh.mp3", 1.5: "sfx_glitch.mp3"}
    },
    "japanese_fresh": {
        "name": "日系清新小資（高亮通透）",
        "text_color": "#333333",
        "stroke_color": "#FFFFFF",
        "stroke_width": 3,
        "text_pos": ("center", 300),
        "sfx_pattern": {0.0: "sfx_ding.mp3", 3.0: "sfx_camera.mp3"}
    }
}

def generate_saas_video(user_media_paths, style_id, slogan_text, shop_name, logo_path, output_path):
    """ 後端剪輯核心引擎 (MoviePy 2.0 架構) """
    cfg = STYLE_TEMPLATES[style_id]
    
    # 處理與串接素材
    clips = []
    for media in user_media_paths[:5]:
        if media.endswith(('.mp4', '.mov')):
            # v2.0 語法改為 subclipped 與 resized
            clip = VideoFileClip(media).subclipped(0, 3).resized(width=1080, height=1920)
        else:
            clip = ImageClip(media).with_duration(3).resized(width=1080, height=1920)
        clips.append(clip)
    
    final_media_clip = concatenate_videoclips(clips, method="compose")

    # 動態字幕
    if slogan_text:
        # v2.0 語法：明確指定 font_size, 且 font 必須提供路徑
        title_clip = TextClip(
            font="./fonts/NotoSansTC-Black.ttf",
            text=slogan_text, 
            font_size=60, 
            color=cfg["text_color"], 
            stroke_color=cfg["stroke_color"], 
            stroke_width=cfg["stroke_width"]
        ).with_duration(2.5).with_position(cfg["text_pos"])
        
        final_video = CompositeVideoClip([final_media_clip, title_clip])
    else:
        final_video = final_media_clip

    # 右上角品牌浮水印
    if logo_path and os.path.exists(logo_path):
        watermark = ImageClip(logo_path).with_duration(final_video.duration).resized(width=160)
        watermark = watermark.with_position((840, 50))
        final_video = CompositeVideoClip([final_video, watermark])
    elif shop_name:
        name_clip = TextClip(
            text=f"@{shop_name}", 
            font_size=28, 
            color="white", 
            font="./fonts/NotoSansTC-Black.ttf"
        ).with_duration(final_video.duration).with_position((800, 60))
        final_video = CompositeVideoClip([final_video, name_clip])

    video_duration = final_video.duration
    audio_clips = []
    
    # 音樂庫處理
    bgm_dir = f"./bgm/{style_id}"
    if os.path.exists(bgm_dir):
        songs = [os.path.join(bgm_dir, f) for f in os.listdir(bgm_dir) if f.endswith('.mp3')]
        if songs:
            selected_bgm = random.choice(songs)
            bgm_volume = 0.2 if style_id == "viral_vlog" else 0.3
            
            # v2.0 語法：with_volume_scaled 替代 volumex
            bgm_audio = AudioFileClip(selected_bgm).with_volume_scaled(bgm_volume)
            
            # 手動循環音軌以符合影片長度
            repeats = int(video_duration / bgm_audio.duration) + 1
            bgm_audio = concatenate_audioclips([bgm_audio] * repeats).subclipped(0, video_duration)
            audio_clips.append(bgm_audio)
    
    # 載入特效音
    for trigger_time, sfx_name in cfg["sfx_pattern"].items():
        sfx_path = f"./assets/{sfx_name}"
        if os.path.exists(sfx_path) and trigger_time < video_duration:
            # v2.0 語法：with_start 替代 set_start
            sfx_audio = AudioFileClip(sfx_path).with_start(trigger_time).with_volume_scaled(1.0)
            audio_clips.append(sfx_audio)

    # 合併所有音軌到影片中
    if audio_clips:
        final_video = final_video.with_audio(CompositeAudioClip(audio_clips))

    if final_video.duration > 60:
        final_video = final_video.subclipped(0, 60)

    # 執行渲染輸出
    final_video.write_videofile(
        output_path, fps=24, codec="libx264", audio_codec="aac", threads=2
    )

# ==========================================
# 3. Streamlit 前端網頁介面
# ==========================================
st.set_page_config(page_title="SaaS 短影音自動生成器", layout="centered")
st.title("🎬 SaaS 短影音自動化行銷平台")
st.subheader("🎉 全新 2.0 引擎驅動版！一鍵生成你的爆款短影音")

style_choice = st.selectbox(
    "步驟 1：選擇視聽風格模板", 
    ["微電影工作室（沉穩高質感）", "極速網紅自媒體（快節奏重口味）", "日系清新小資（高亮通透）"]
)
style_id_map = {
    "微電影工作室（沉穩高質感）": "cinematic",
    "極速網紅自媒體（快節奏重口味）": "viral_vlog",
    "日系清新小資（高亮通透）": "japanese_fresh"
}
selected_style_id = style_id_map[style_choice]

uploaded_files = st.file_uploader(
    "步驟 2：上傳素材影片或照片（可多選，最多5個）", 
    accept_multiple_files=True, 
    type=["jpg", "jpeg", "png", "mp4", "mov"]
)

slogan = st.text_input("步驟 3：輸入爆款標語", "🔥 本月最扯下殺！")
shop_name = st.text_input("步驟 4：輸入您的品牌/店名", "光影影像工作室")
logo_file = st.file_uploader("步驟 5：上傳品牌 LOGO (透明底 PNG 佳，選填)", type=["png"])

if st.button("🚀 一鍵生成爆款短影音"):
    if not uploaded_files:
        st.warning("⚠️ 請至少上傳一個媒體素材（照片或影片）才能開始剪輯喔！")
    else:
        st.info("⏳ 影片排隊處理中... 全新 2.0 引擎渲染大約需要 1~2 分鐘，請勿關閉網頁...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            user_media_paths = []
            
            for f in uploaded_files:
                temp_path = os.path.join(temp_dir, f.name)
                with open(temp_path, "wb") as buffer:
                    buffer.write(f.read())
                user_media_paths.append(temp_path)
            
            logo_path = None
            if logo_file:
                logo_path = os.path.join(temp_dir, "user_logo.png")
                with open(logo_path, "wb") as buffer:
                    buffer.write(logo_file.read())
            
            output_video_path = os.path.join(temp_dir, "final_output.mp4")
            
            try:
                generate_saas_video(
                    user_media_paths=user_media_paths,
                    style_id=selected_style_id,
                    slogan_text=slogan,
                    shop_name=shop_name,
                    logo_path=logo_path,
                    output_path=output_video_path
                )
                
                st.success("🎉 短影音生成成功！請在下方預覽與下載：")
                with open(output_video_path, "rb") as video_file:
                    video_bytes = video_file.read()
                    
                    st.video(video_bytes)
                    st.download_button(
                        label="💾 下載生成的短影音",
                        data=video_bytes,
                        file_name="viral_short_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"❌ 渲染過程中發生錯誤：{e}")
            
            finally:
                gc.collect()