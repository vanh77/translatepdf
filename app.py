import base64
import io
import re
from google import genai
from PIL import Image, ImageEnhance # <--- Đã thêm thư viện xử lý ảnh
import streamlit as st
import weasyprint

st.set_page_config(page_title="Dịch Sách Chuẩn Layout 3D", page_icon="📚", layout="wide")

st.markdown("""
<style>
    .stButton>button { font-weight: bold; font-size: 16px; }
    div[data-testid="stSidebar"] { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("📚 Dịch Sách (Bảo Toàn 100% Hình Ảnh Sinh Động)")

with st.sidebar:
    st.header("⚙️ Cài Đặt")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    
    target_language = st.radio(
        "🌐 Chọn ngôn ngữ đích:",
        ("Tiếng Việt (Vietnamese)", "Tiếng Anh (English)"),
        index=0
    )

if not api_key:
    st.info("👈 Vui lòng nhập API Key ở thanh bên trái.")
    st.stop()

client = genai.Client(api_key=api_key)

uploaded_file = st.file_uploader(
    "Tải ảnh trang sách lên...", type=["jpg", "png", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    img_width, img_height = image.size

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🖼️ Ảnh gốc")
        st.image(image, use_container_width=True)

    with col2:
        st.subheader("⚙️ Trạng thái xử lý")
        
        if st.button("🚀 Dịch & Hòa Quyện Hình Ảnh", type="primary", use_container_width=True):
            
            with st.spinner("AI đang tính toán bố cục và tẩy trắng phông nền..."):
                try:
                    lang_code = "Tiếng Việt" if "Việt" in target_language else "English"
                    
                    # PROMPT V4.1 - ÉP BỐ CỤC SINH ĐỘNG VÀ TUYỆT ĐỐI CẤM SVG
                    prompt = f"""
                    Bạn là một chuyên gia dàn trang HTML/CSS xuất sắc.
                    Hãy đọc ảnh trang sách này, tái tạo lại toàn bộ bố cục, dịch chữ sang {lang_code}.

                    QUY TẮC SỐ 1 - HÌNH ẢNH SINH ĐỘNG:
                    - TUYỆT ĐỐI KHÔNG dùng mã SVG, Canvas hay CSS để tự vẽ lại bất kỳ họa tiết nào (nhân vật, ngôi sao, hình khối 3D). Đừng cố vẽ, nó sẽ làm hỏng tính sinh động!
                    - Thay vào đó, BẮT BUỘC dùng <CROP_IMAGE ymin="Y1" xmin="X1" ymax="Y2" xmax="X2"></CROP_IMAGE> cho MỌI HÌNH VẼ (kể cả những ngôi sao nhỏ rải rác hay nhân vật phù thủy góc dưới).
                    - Để sắp xếp chúng sinh động lồng vào chữ như bản gốc, hãy bọc <CROP_IMAGE> trong các thẻ div có style như `position: absolute; right: 10%; bottom: 5%;` hoặc `float: right; margin: 10px;` tùy vào vị trí.

                    QUY TẮC SỐ 2 - BỐ CỤC & BẢNG BIỂU:
                    - Dịch đầy đủ các bảng dữ liệu (Table) ở đầu trang.
                    - Giữ nguyên cấu trúc câu hỏi 9 đến 15. Dùng HTML structure gọn gàng.
                    
                    CSS CHUẨN:
                    <style>
                        @page {{ size: A4 portrait; margin: 10mm 15mm; }}
                        body {{ font-family: sans-serif; font-size: 10.5pt; line-height: 1.4; color: #333; position: relative; }}
                        p, div, h1, h2, h3 {{ margin: 0 0 6px 0; padding: 0; }}
                        table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; font-size: 9pt; }}
                        th, td {{ border: 1px solid #999; padding: 4px; text-align: center; }}
                        th {{ background-color: #f2f2f2; font-weight: bold; }}
                    </style>
                    """

                    response = client.models.generate_content(
                        model="gemini-3.5-flash", contents=[image, prompt]
                    )

                    html_code = response.text
                    html_code = re.sub(r"^```html\s*", "", html_code, flags=re.MULTILINE)
                    html_code = re.sub(r"^```\s*", "", html_code, flags=re.MULTILINE)

                    # --- HÀM CẮT ẢNH VÀ TẨY TRẮNG NỀN THÔNG MINH ---
                    def replace_crop_tag(match):
                        try:
                            ymin = int(match.group("ymin"))
                            xmin = int(match.group("xmin"))
                            ymax = int(match.group("ymax"))
                            xmax = int(match.group("xmax"))

                            left = (xmin / 1000.0) * img_width
                            top = (ymin / 1000.0) * img_height
                            right = (xmax / 1000.0) * img_width
                            bottom = (ymax / 1000.0) * img_height

                            # Cắt ảnh
                            cropped_img = image.crop((max(0, left-2), max(0, top-2), min(img_width, right+2), min(img_height, bottom+2)))

                            # THUẬT TOÁN TẨY TRẮNG NỀN GIẤY:
                            # 1. Tăng độ tương phản (Contrast) lên 20%
                            enhancer_contrast = ImageEnhance.Contrast(cropped_img)
                            cropped_img = enhancer_contrast.enhance(1.2)
                            
                            # 2. Tăng độ sáng (Brightness) lên 15% -> Giúp màu giấy xám thành màu trắng tinh
                            enhancer_brightness = ImageEnhance.Brightness(cropped_img)
                            cropped_img = enhancer_brightness.enhance(1.15)

                            # Đóng gói ảnh thành chuỗi Base64
                            buffered = io.BytesIO()
                            cropped_img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()

                            # Chèn ảnh, dùng style CSS blend-mode (hỗ trợ hiển thị hài hòa hơn)
                            return f'<img src="data:image/png;base64,{img_str}" style="max-width: 100%; height: auto; display: block; mix-blend-mode: multiply;"/>'
                        except Exception:
                            return ""

                    final_html = re.sub(r'<CROP_IMAGE\s+ymin="(?P<ymin>\d+)"\s+xmin="(?P<xmin>\d+)"\s+ymax="(?P<ymax>\d+)"\s+xmax="(?P<xmax>\d+)"></CROP_IMAGE>', replace_crop_tag, html_code)

                    st.toast('Đã phân tích xong trang sách!', icon='✅')

                    pdf_bytes = weasyprint.HTML(string=final_html).write_pdf()

                    st.success("🎉 Hoàn tất! Các nhân vật 3D đã được hòa quyện vào trang giấy.")
                    
                    st.download_button(
                        label="📥 Tải File PDF Về Máy",
                        data=pdf_bytes,
                        file_name=f"Trang_Sach_{lang_code[:2].upper()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")
