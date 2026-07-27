import base64
import io
import re
from google import genai
from PIL import Image
import streamlit as st
import weasyprint

st.set_page_config(page_title="Dịch Sách Chuẩn 2 Cột", page_icon="📚", layout="wide")

st.markdown("""
<style>
    .stButton>button { font-weight: bold; font-size: 16px; }
    div[data-testid="stSidebar"] { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("📚 Dịch Sách Giáo Khoa (Bố Cục 2 Cột & Tẩy Nền Sạch 100%)")

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
        
        if st.button("🚀 Dịch & Dàn Trang 2 Cột Hoàn Hảo", type="primary", use_container_width=True):
            
            with st.spinner("AI đang xử lý bố cục 2 cột và làm sạch hình ảnh..."):
                try:
                    lang_code = "Tiếng Việt" if "Việt" in target_language else "English"
                    
                    # PROMPT V5.0 - ÉP BỐ CỤC 2 CỘT CHUẨN SÁCH GỐC
                    prompt = f"""
                    Bạn là một chuyên gia dàn trang sách giáo khoa xuất sắc.
                    Hãy đọc ảnh trang sách này, dịch toàn bộ nội dung sang {lang_code} và tạo mã HTML5 hoàn chỉnh.

                    QUY TẮC DÀN TRANG (QUAN TRỌNG NHẤT):
                    1. BỐ CỤC 2 CỘT: Trang sách gốc có 2 cột (Cột trái gồm Bài 1, 2, 3; Cột phải gồm Bài 4, 5...). Bạn BẮT BUỘC phải dùng CSS multi-column hoặc chia khung để giữ nguyên cấu trúc 2 cột này. Không được xếp dọc đơn thuần.
                    2. KHÔNG CẮT XÉN: Đảm bảo dịch và hiển thị đầy đủ từ tiêu đề đầu trang đến bài tập cuối cùng ở chân trang.
                    3. HÌNH ẢNH: Sử dụng thẻ <CROP_IMAGE ymin="Y1" xmin="X1" ymax="Y2" xmax="X2"></CROP_IMAGE> cho mọi hình minh họa, xúc xắc, khối 3D.
                    4. TRÌNH BÀY PHÂN SỐ: Phân số phải được viết gọn gàng trong 1 dòng bằng thẻ span nội tuyến có gạch chân ở giữa để không làm vỡ khoảng cách dòng.

                    CSS CHUẨN ĐỂ ÉP VỪA KHÍT 1 TRANG A4 VÀ 2 CỘT:
                    <style>
                        @page {{ 
                            size: A4 portrait; 
                            margin: 10mm; 
                        }}
                        body {{ 
                            font-family: Arial, sans-serif; 
                            font-size: 8.5pt; 
                            line-height: 1.25; 
                            color: #222; 
                        }}
                        /* Ép toàn bộ nội dung chia thành 2 cột đúng chuẩn sách giáo khoa */
                        .book-page {{
                            column-count: 2;
                            column-gap: 15px;
                            height: 275mm; /* Khớp chiều cao A4 */
                            box-sizing: border-box;
                        }}
                        /* Ngăn các khối bài tập bị ngắt trang xấu xí */
                        .exercise, div, p {{
                            break-inside: avoid;
                            margin-bottom: 6px;
                        }}
                        h1, h2, h3 {{ margin: 0 0 5px 0; }}
                        .box-tieu-de {{ 
                            background: #d9534f; color: white; padding: 4px 8px; 
                            font-weight: bold; border-radius: 4px; display: inline-block; font-size: 10pt;
                        }}
                        img {{ 
                            max-width: 100%; 
                            height: auto; 
                            display: block; 
                            margin: 3px auto; 
                        }}
                    </style>
                    
                    Bọc toàn bộ nội dung trang sách bên trong thẻ: <div class="book-page"> ... nội dung ... </div>
                    Chỉ trả về mã HTML hoàn chỉnh, không kèm markdown code block.
                    """

                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite", contents=[image, prompt]
                    )

                    html_code = response.text
                    html_code = re.sub(r"^```html\s*", "", html_code, flags=re.MULTILINE)
                    html_code = re.sub(r"^```\s*", "", html_code, flags=re.MULTILINE)

                    # --- HÀM CẮT ẢNH VÀ TẨY NỀN SẠCH 100% ---
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

                            # Cắt ảnh chuẩn xác
                            cropped_img = image.crop((max(0, left-2), max(0, top-2), min(img_width, right+2), min(img_height, bottom+2)))

                            # THUẬT TOÁN TẨY NỀN Ố VÀNG THÀNH TRẮNG TINH:
                            cropped_img = cropped_img.convert("RGBA")
                            datas = cropped_img.getdata()
                            new_data = []
                            for item in datas:
                                r, g, b, a = item
                                # Nếu pixel có màu sáng (gần giống màu nền giấy cũ/trắng ngà), đổi thành trắng tinh
                                if r > 185 and g > 185 and b > 175 and abs(r - g) < 25 and abs(g - b) < 25:
                                    new_data.append((255, 255, 255, 255))
                                else:
                                    new_data.append(item)
                            cropped_img.putdata(new_data)
                            cropped_img = cropped_img.convert("RGB")

                            # Lưu vào bộ nhớ đệm dạng Base64
                            buffered = io.BytesIO()
                            cropped_img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()

                            return f'<img src="data:image/png;base64,{img_str}" style="max-width: 100%; height: auto; display: block;"/>'
                        except Exception as e:
                            print(f"Lỗi crop: {e}")
                            return ""

                    final_html = re.sub(r'<CROP_IMAGE\s+ymin="(?P<ymin>\d+)"\s+xmin="(?P<xmin>\d+)"\s+ymax="(?P<ymax>\d+)"\s+xmax="(?P<xmax>\d+)"></CROP_IMAGE>', replace_crop_tag, html_code)

                    st.toast('Đã phân tích xong!', icon='✅')

                    # Xuất PDF bằng Weasyprint
                    pdf_bytes = weasyprint.HTML(string=final_html).write_pdf()

                    st.success("🎉 Hoàn tất! Trang sách đã được tối ưu bố cục 2 cột và làm sạch nền tuyệt đối.")
                    
                    st.download_button(
                        label="📥 Tải File PDF Về Máy",
                        data=pdf_bytes,
                        file_name=f"Trang_Sach_Chuan_{lang_code[:2].upper()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")
