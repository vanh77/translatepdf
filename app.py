import base64
import io
import re
from google import genai
from PIL import Image
import streamlit as st
import weasyprint

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Dịch Sách PDF Tự Động", page_icon="📚", layout="wide"
)

# Thêm CSS để giao diện gọn gàng hơn
st.markdown("""
<style>
    .stButton>button { font-weight: bold; font-size: 16px; }
    div[data-testid="stSidebar"] { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("📚 Dịch Sách Giáo Khoa (Đảm Bảo Hình Gốc 100% & Ép Vừa 1 Trang)")

# --- MENU BÊN TRÁI ---
with st.sidebar:
    st.header("⚙️ Cài Đặt Hệ Thống")
    
    # 1. Nhập API Key (Nếu chạy local thì có thể dùng st.secrets)
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    
    st.markdown("---")
    
    # 2. CÔNG TẮC CHỌN NGÔN NGỮ (Tính năng mới)
    target_language = st.radio(
        "🌐 Chọn ngôn ngữ đích muốn dịch sang:",
        ("Tiếng Việt (Vietnamese)", "Tiếng Anh (English)"),
        index=0
    )
    
    st.markdown("---")
    st.write("💡 *Mẹo: Đảm bảo ảnh chụp trang sách ngay ngắn, đủ sáng để AI lấy tọa độ hình cắt chuẩn nhất.*")


if not api_key:
    st.info("👈 Vui lòng nhập API Key ở thanh bên trái để bắt đầu.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- KHU VỰC TẢI ẢNH ---
uploaded_file = st.file_uploader(
    "Tải ảnh một trang sách lên (JPG, PNG)...", type=["jpg", "png", "jpeg"]
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
        
        if st.button("🚀 Xử Lý & Xuất PDF Ngay", type="primary", use_container_width=True):
            
            with st.spinner(f"AI đang phân tích, cắt hình gốc và dịch sang {target_language}..."):
                try:
                    # Rút trích ngôn ngữ chỉ định từ lựa chọn
                    lang_code = "Tiếng Việt" if "Việt" in target_language else "English"
                    
                    # PROMPT ĐÃ ĐƯỢC CẢI TIẾN THÊM CSS ÉP VỪA 1 TRANG (Fit-to-page)
                    prompt = f"""
                    Bạn là một chuyên gia dàn trang sách giáo khoa xuất sắc.
                    Hãy đọc ảnh trang sách này và tạo lại trang sách bằng mã HTML5. Toàn bộ chữ viết phải được dịch sang {lang_code}.

                    YÊU CẦU KIỂM SOÁT HÌNH ẢNH:
                    - TUYỆT ĐỐI KHÔNG vẽ lại các hình 3D, xúc xắc, khối hộp, sơ đồ hay hình minh họa phức tạp.
                    - Để giữ 100% hình gốc, bạn hãy đánh dấu vị trí hình đó trong cấu trúc HTML bằng thẻ <CROP_IMAGE ymin="Y1" xmin="X1" ymax="Y2" xmax="X2"></CROP_IMAGE>.
                    - Tọa độ Y1, X1, Y2, X2 phải được chuẩn hóa theo thang điểm từ 0 đến 1000 bao trọn vùng hình ảnh đó. (X là ngang, Y là dọc).

                    YÊU CẦU KIỂM SOÁT BỐ CỤC (ÉP VỪA 1 TRANG):
                    1. Bố cục: Giữ nguyên cấu trúc 2 cột, bảng biểu, hộp màu như trang gốc.
                    2. Dịch thuật: Dịch toàn bộ văn bản sang {lang_code}. Cố gắng diễn đạt ngắn gọn để không chiếm quá nhiều diện tích.
                    3. CSS Ép Khung (BẮT BUỘC): Thêm đoạn CSS sau vào thẻ <head> để đảm bảo toàn bộ nội dung thu nhỏ vừa khít 1 trang A4, tuyệt đối không bị tràn sang trang 2:
                    
                    <style>
                        @page {{
                            size: A4 portrait;
                            margin: 10mm;
                        }}
                        body {{
                            width: 100%;
                            height: 277mm; /* Chiều cao A4 trừ đi lề */
                            overflow: hidden; /* Cắt bớt phần thừa nếu có */
                            box-sizing: border-box;
                            font-size: 11pt; /* Chữ vừa phải */
                            display: flex;
                            flex-direction: column;
                        }}
                        .main-container {{
                            flex: 1; /* Tự động co giãn theo chiều dọc */
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between; /* Giãn đều khoảng cách */
                        }}
                        img {{
                            max-height: 150px; /* Giới hạn chiều cao hình ảnh để không chiếm chỗ */
                            object-fit: contain;
                        }}
                    </style>
                    
                    Bọc toàn bộ nội dung body vào thẻ <div class="main-container">...</div>.
                    Chỉ trả về mã HTML hoàn chỉnh, không kèm markdown (không dùng ```html).
                    """

                    # Gọi API Gemini
                    response = client.models.generate_content(
                        model="gemini-3.5-flash", contents=[image, prompt]
                    )

                    html_code = response.text
                    
                    # Dọn dẹp mã markdown
                    html_code = re.sub(r"^```html\s*", "", html_code, flags=re.MULTILINE)
                    html_code = re.sub(r"^```\s*", "", html_code, flags=re.MULTILINE)

                    # --- HÀM CẮT ẢNH GỐC ---
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

                            # Cắt và mở rộng lề một chút (+-5px) để khỏi mất nét viền
                            cropped_img = image.crop((max(0, left-5), max(0, top-5), min(img_width, right+5), min(img_height, bottom+5)))

                            buffered = io.BytesIO()
                            cropped_img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()

                            # Chèn ảnh đã cắt, CSS tự động bóp nhỏ nếu ảnh quá to để không bị tràn trang
                            return f'<img src="data:image/png;base64,{img_str}" style="max-width:100%; display:block; margin: 4px auto; border-radius: 4px;"/>'
                        except Exception as e:
                            print(f"Lỗi crop ảnh: {e}")
                            return ""

                    # Thay thế thẻ CROP_IMAGE bằng ảnh thật
                    pattern = r'<CROP_IMAGE\s+ymin="(?P<ymin>\d+)"\s+xmin="(?P<xmin>\d+)"\s+ymax="(?P<ymax>\d+)"\s+xmax="(?P<xmax>\d+)"></CROP_IMAGE>'
                    final_html = re.sub(pattern, replace_crop_tag, html_code)

                    st.toast('Đã phân tích xong trang sách!', icon='✅')

                    # CHUYỂN ĐỔI SANG PDF VỚI WEASYPRINT
                    pdf_bytes = weasyprint.HTML(string=final_html).write_pdf()

                    st.success(f"🎉 Hoàn tất! Trang sách đã được dịch sang {lang_code} và ép vừa đúng 1 trang.")
                    
                    file_name_export = "Trang_Sach_VN.pdf" if lang_code == "Tiếng Việt" else "Trang_Sach_EN.pdf"
                    
                    st.download_button(
                        label="📥 Tải File PDF Về Máy",
                        data=pdf_bytes,
                        file_name=file_name_export,
                        mime="application/pdf",
                        use_container_width=True
                    )

                    with st.expander("🔍 Xem mã nguồn HTML (Dành cho nhà phát triển)"):
                        st.code(final_html, language="html")

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")
