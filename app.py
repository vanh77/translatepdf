import io
import re
import streamlit as st
from PIL import Image
from google import genai
import weasyprint

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Dịch & Dàn Trang Sách Tự Động", page_icon="📚", layout="wide")

st.title("📚 Chuyển Ảnh Sách Giáo Khoa -> PDF Tiếng Việt")
st.write("Ứng dụng tự động dịch chữ và phục dựng nguyên bản bố cục trang sách thành file PDF nét căng.")

# --- MENU BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
    st.markdown("[Lấy API key miễn phí tại đây](https://aistudio.google.com/app/apikey)")
    st.write("---")
    st.write("👩‍🏫 **Dành cho Giáo viên & Gia sư**")
    st.write("Hỗ trợ xuất PDF chuẩn in ấn A4, vẽ lại sơ đồ bằng vector.")

# --- KIỂM TRA API KEY ---
if not api_key:
    st.info("👈 Vui lòng nhập API Key ở menu bên trái để bắt đầu.")
    st.stop()

# Khởi tạo client AI
client = genai.Client(api_key=api_key)

# --- UPLOAD ẢNH ---
uploaded_file = st.file_uploader("Tải ảnh trang sách giáo khoa lên (JPG, PNG)...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Chia giao diện làm 2 cột
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ảnh gốc")
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    with col2:
        st.subheader("Trạng thái xử lý")
        if st.button("🚀 Bắt đầu Dịch & Tạo PDF", type="primary", use_container_width=True):
            with st.spinner("AI đang phân tích bố cục, vẽ hình và dịch thuật (khoảng 15-30 giây)..."):
                try:
                    prompt = """
                    Bạn là một chuyên gia dàn trang sách giáo khoa kiêm lập trình viên HTML/CSS xuất sắc.
                    Hãy đọc ảnh trang sách này và tạo lại TRANG SÁCH ĐÃ DỊCH SANG TIẾNG VIỆT dưới dạng 1 file HTML5 hoàn chỉnh.

                    YÊU CẦU:
                    1. BỐ CỤC: Giữ nguyên cấu trúc trang sách gốc (chia cột, khung viền, màu sắc, vị trí bài tập).
                    2. NỘI DUNG: Dịch toàn bộ nội dung sang Tiếng Việt một cách tự nhiên.
                    3. HÌNH VẼ HÌNH HỌC: Vẽ lại các hình vẽ, sơ đồ bằng mã SVG (<svg>).
                    4. BẢNG BIỂU: Dùng HTML <table> cho các ô chữ, bảng số liệu, mê cung. Căn chỉnh border, background chuẩn xác.
                    5. Khổ A4: CSS có @page { size: A4 portrait; margin: 15mm; }
                    6. FONT CHỮ: Dùng font sans-serif cơ bản, dễ đọc.

                    Chỉ trả về DUY NHẤT mã HTML hoàn chỉnh, không có markdown fenced code block (không dùng ```html), không giải thích gì thêm.
                    """
                    
                    # Gọi API Gemini Flash (Rất nhanh và thông minh)
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=[image, prompt]
                    )
                    
                    html_code = response.text
                    
                    # Dọn dẹp mã markdown nếu AI lỡ thêm vào
                    html_code = re.sub(r"^```html\s*", "", html_code, flags=re.MULTILINE)
                    html_code = re.sub(r"^```\s*", "", html_code, flags=re.MULTILINE)

                    st.toast('Đã sinh xong mã HTML!', icon='✅')

                    # Xuất PDF bằng WeasyPrint
                    pdf_bytes = weasyprint.HTML(string=html_code).write_pdf()
                    
                    st.success("🎉 Hoàn tất! File PDF đã sẵn sàng để in.")
                    
                    # Nút tải xuống file PDF
                    st.download_button(
                        label="📥 Tải File PDF Trang Sách",
                        data=pdf_bytes,
                        file_name="Trang_Sach_Dich.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    # Cho phép xem mã HTML gốc nếu muốn kiểm tra
                    with st.expander("Xem mã HTML/CSS gốc (Dành cho lập trình viên)"):
                        st.code(html_code, language="html")

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
