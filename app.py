import base64
import io
import re
from google import genai
from PIL import Image
import streamlit as st
import weasyprint

st.set_page_config(
    page_title="Dịch Sách Chuẩn Hình Ảnh 100%", page_icon="📚", layout="wide"
)
st.title("📚 Dịch Sách Giáo Khoa (Giữ Nguyên 100% Hình Minh Họa 3D)")

api_key = st.sidebar.text_input("Nhập Google Gemini API Key:", type="password")

if api_key:
  client = genai.Client(api_key=api_key)

  uploaded_file = st.file_uploader(
      "Tải ảnh trang sách lên...", type=["jpg", "png", "jpeg"]
  )

  if uploaded_file:
    image = Image.open(uploaded_file)
    img_width, img_height = image.size

    col1, col2 = st.columns(2)
    with col1:
      st.image(image, caption="Ảnh gốc", use_container_width=True)

    with col2:
      if st.button(
          "🚀 Bắt đầu Dịch & Xử lý Chuẩn 100%",
          type="primary",
          use_container_width=True,
      ):
        with st.spinner("AI đang dịch chữ và trích xuất hình ảnh..."):
          try:
            # CẬP NHẬT PROMPT: Ép CSS chuẩn cho Weasyprint để chống nhảy trang
            prompt = """
                        Bạn là một chuyên gia dàn trang sách giáo khoa bằng HTML5 và CSS.
                        Hãy đọc ảnh trang sách này và tạo lại TRANG SÁCH ĐÃ DỊCH SANG TIẾNG VIỆT.

                        QUY TẮC CSS (RẤT QUAN TRỌNG ĐỂ KHÔNG BỊ LỖI PDF):
                        1. Khổ giấy: @page { size: A4 portrait; margin: 15mm; }
                        2. Layout 2 cột: KHÔNG dùng display: flex hay grid cho 2 cột chính. BẮT BUỘC dùng CSS Columns:
                           .two-columns { column-count: 2; column-gap: 30px; }
                        3. Chống nhảy trang (Lỗi khoảng trắng): Với mỗi block bài tập, BẮT BUỘC thêm CSS: `break-inside: avoid; page-break-inside: avoid;` để nội dung không bị vỡ và đẩy xuống trang dưới.
                        4. Hình ảnh: Các hình ảnh phải có `max-width: 100%; height: auto; display: block; margin: 10px auto;`.

                        QUY TẮC XỬ LÝ HÌNH VẼ 3D / BẢNG BIỂU:
                        - Tuyệt đối KHÔNG tự vẽ lại bằng SVG, CSS, hay ký tự.
                        - Với MỖI hình minh họa, hãy chèn chính xác chuỗi sau (giữ đúng thứ tự ymin, xmin, ymax, xmax):
                          <CROP_IMAGE ymin="Y1" xmin="X1" ymax="Y2" xmax="X2"></CROP_IMAGE>
                          (Tọa độ từ 0 đến 1000 theo tỷ lệ ảnh).

                        Chỉ trả về mã HTML hoàn chỉnh, không có markdown code block (không bắt đầu bằng ```html).
                        """

            # Lưu ý: Kiểm tra lại tên model, hiện tại chuẩn là gemini-1.5-flash hoặc gemini-2.0-flash
            response = client.models.generate_content(
                model="gemini-3.5-flash", contents=[image, prompt]
            )

            html_code = response.text
            html_code = re.sub(
                r"^```html\s*", "", html_code, flags=re.MULTILINE
            )
            html_code = re.sub(r"^```\s*", "", html_code, flags=re.MULTILINE)

            # --- BƯỚC XỬ LÝ CẮT ẢNH TỰ ĐỘNG BẰNG PYTHON ---
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

                cropped_img = image.crop((left, top, right, bottom))

                buffered = io.BytesIO()
                cropped_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                return f'<img src="data:image/png;base64,{img_str}" style="max-width:100%; height:auto; display:block; margin: 10px auto;"/>'
              except Exception:
                return ""

            # Regex đã được nới lỏng để bắt thẻ tốt hơn dù AI có sinh ra thẻ tự đóng hay có khoảng trắng thừa
            pattern = r'<CROP_IMAGE\s+ymin="(?P<ymin>\d+)"\s+xmin="(?P<xmin>\d+)"\s+ymax="(?P<ymax>\d+)"\s+xmax="(?P<xmax>\d+)"[^>]*>(?:</CROP_IMAGE>)?'
            final_html = re.sub(pattern, replace_crop_tag, html_code)

            # Chuyển thành PDF
            pdf_bytes = weasyprint.HTML(string=final_html).write_pdf()

            st.success("🎉 Hoàn tất! File PDF đã được canh chỉnh lại layout.")
            st.download_button(
                label="📥 Tải File PDF Trang Sách",
                data=pdf_bytes,
                file_name="Trang_Sach_Chuan_100.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

          except Exception as e:
            st.error(f"Lỗi xử lý: {e}")
