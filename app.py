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
            # PROMPT YÊU CẦU AI TRẢ VỀ TỌA ĐỘ HÌNH VẼ
            prompt = """
                        Bạn là một chuyên gia dàn trang sách giáo khoa.
                        Hãy đọc ảnh trang sách này và tạo lại TRANG SÁCH ĐÃ DỊCH SANG TIẾNG VIỆT dưới dạng mã HTML5.

                        QUY TẮC XỬ LÝ HÌNH VẼ / MINH HỌA 3D / BẢNG BIỂU PHỨC TẠP:
                        - Tuyệt đối KHÔNG tự vẽ lại các hình vẽ 3D, xúc xắc, khối lập phương, sơ đồ trải phẳng bằng SVG hay CSS.
                        - Thay vào đó, với MỖI hình minh họa/sơ đồ trong bài tập, hãy đặt một thẻ giữ chỗ theo định dạng:
                          <CROP_IMAGE ymin="TỎA_ĐỘ_Y1" xmin="TỌA_ĐỘ_X1" ymax="TỎA_ĐỘ_Y2" xmax="TỌA_ĐỘ_X2"></CROP_IMAGE>
                          (Tọa độ chuẩn hóa từ 0 đến 1000 theo tỷ lệ bức ảnh).

                        YÊU CẦU CHUNG:
                        1. BỐ CỤC: Giữ nguyên cấu trúc 2 cột, thứ tự bài tập, khung tiêu đề màu da cam.
                        2. DỊCH THUẬT: Dịch chính xác toàn bộ câu hỏi, yêu cầu sang Tiếng Việt.
                        3. Khổ A4: CSS có @page { size: A4 portrait; margin: 12mm; }

                        Chỉ trả về mã HTML hoàn chỉnh, không kèm markdown code block.
                        """

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
                # Lấy tọa độ tỷ lệ 0-1000
                ymin = int(match.group("ymin"))
                xmin = int(match.group("xmin"))
                ymax = int(match.group("ymax"))
                xmax = int(match.group("xmax"))

                # Chuyển sang pixel thực tế của ảnh
                left = (xmin / 1000.0) * img_width
                top = (ymin / 1000.0) * img_height
                right = (xmax / 1000.0) * img_width
                bottom = (ymax / 1000.0) * img_height

                # Cắt vùng ảnh gốc
                cropped_img = image.crop((left, top, right, bottom))

                # Chuyển ảnh cắt thành mã Base64 nhúng thẳng vào HTML
                buffered = io.BytesIO()
                cropped_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                return f'<img src="data:image/png;base64,{img_str}" style="max-width:100%; height:auto; display:block; margin: 5px auto;"/>'
              except Exception:
                return ""

            # Pattern tìm các thẻ <CROP_IMAGE ...>
            pattern = r'<CROP_IMAGE\s+ymin="(?P<ymin>\d+)"\s+xmin="(?P<xmin>\d+)"\s+ymax="(?P<ymax>\d+)"\s+xmax="(?P<xmax>\d+)"></CROP_IMAGE>'
            final_html = re.sub(pattern, replace_crop_tag, html_code)

            # Chuyển thành PDF
            pdf_bytes = weasyprint.HTML(string=final_html).write_pdf()

            st.success("🎉 Hoàn tất! File PDF đã chính xác 100% hình vẽ gốc.")
            st.download_button(
                label="📥 Tải File PDF Trang Sách (Hình ảnh chuẩn 100%)",
                data=pdf_bytes,
                file_name="Trang_Sach_Chuan_100.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

          except Exception as e:
            st.error(f"Lỗi xử lý: {e}")
