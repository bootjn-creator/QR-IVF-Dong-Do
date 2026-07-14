from __future__ import annotations

import io
import re
from pathlib import Path
from urllib.parse import urlparse

import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageOps


APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "logo_ivf_dong_do.png"

COLOR_THEMES = {
    "Grey": {"qr": "#7A7F87"},
    "Xanh Đông Đô IVF": {"qr": "#172C74"},
    "Hồng IVF Đông Đô": {"qr": "#EB2374"},
    "Xanh ngọc": {"qr": "#00796B"},
}

QUALITY_OPTIONS = {
    "Tiêu chuẩn": 16,
    "Chất lượng cao": 24,
    "Dùng để in ấn": 32,
}

DOT_STYLE_OPTIONS = [
    "Chấm tròn",
    "Trái tim nhỏ",
]


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def normalize_url(value: str) -> str:
    value = value.strip()

    if value and "://" not in value:
        value = "https://" + value

    return value


def is_valid_web_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and "." in parsed.netloc
        )
    except ValueError:
        return False


def safe_filename(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^\w\- ]+", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._-")

    return value or "qr_ivf_dong_do"


def is_finder_module(
    row: int,
    col: int,
    matrix_size: int,
    border: int,
) -> bool:
    start = border
    end = matrix_size - border

    top_left = (
        start <= row < start + 7
        and start <= col < start + 7
    )

    top_right = (
        start <= row < start + 7
        and end - 7 <= col < end
    )

    bottom_left = (
        end - 7 <= row < end
        and start <= col < start + 7
    )

    return top_left or top_right or bottom_left


def prepare_logo(
    logo_path: Path,
    diameter: int,
    border_color: tuple[int, int, int],
) -> Image.Image:
    logo = Image.open(logo_path).convert("RGBA")

    alpha_bbox = logo.getchannel("A").getbbox()
    if alpha_bbox:
        logo = logo.crop(alpha_bbox)

    content_limit = int(diameter * 0.84)

    logo = ImageOps.contain(
        logo,
        (content_limit, content_limit),
        method=Image.Resampling.LANCZOS,
    )

    circle = Image.new(
        "RGBA",
        (diameter, diameter),
        (255, 255, 255, 0),
    )

    circle_draw = ImageDraw.Draw(circle)

    inset = max(2, diameter // 90)

    circle_draw.ellipse(
        (
            inset,
            inset,
            diameter - inset - 1,
            diameter - inset - 1,
        ),
        fill=(255, 255, 255, 255),
        outline=(*border_color, 255),
        width=max(4, diameter // 65),
    )

    x = (diameter - logo.width) // 2
    y = (diameter - logo.height) // 2

    circle.alpha_composite(logo, (x, y))

    mask = Image.new(
        "L",
        (diameter, diameter),
        0,
    )

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.ellipse(
        (0, 0, diameter - 1, diameter - 1),
        fill=255,
    )

    circle.putalpha(mask)

    return circle


def draw_heart(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    fill: tuple[int, int, int],
) -> None:
    left, top, right, bottom = box

    width = right - left
    height = bottom - top
    center_x = left + width / 2

    radius = width * 0.24
    center_y = top + height * 0.34

    draw.ellipse(
        (
            center_x - 2 * radius,
            center_y - radius,
            center_x,
            center_y + radius,
        ),
        fill=fill,
    )

    draw.ellipse(
        (
            center_x,
            center_y - radius,
            center_x + 2 * radius,
            center_y + radius,
        ),
        fill=fill,
    )

    draw.polygon(
        [
            (
                center_x - width * 0.45,
                top + height * 0.40,
            ),
            (
                center_x,
                bottom - height * 0.10,
            ),
            (
                center_x + width * 0.45,
                top + height * 0.40,
            ),
        ],
        fill=fill,
    )


def create_branded_qr(
    data: str,
    logo_path: Path,
    qr_color: tuple[int, int, int],
    box_size: int,
    logo_percent: int,
    dot_style: str,
) -> Image.Image:
    border = 4

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    matrix_size = len(matrix)
    image_size = matrix_size * box_size

    image = Image.new(
        "RGB",
        (image_size, image_size),
        "white",
    )

    draw = ImageDraw.Draw(image)

    dot_margin = max(
        1,
        round(box_size * 0.10),
    )

    for row in range(matrix_size):
        for col in range(matrix_size):
            if not matrix[row][col]:
                continue

            left = col * box_size
            top = row * box_size
            right = left + box_size - 1
            bottom = top + box_size - 1

            if is_finder_module(
                row,
                col,
                matrix_size,
                border,
            ):
                draw.rounded_rectangle(
                    (
                        left,
                        top,
                        right,
                        bottom,
                    ),
                    radius=max(1, box_size // 8),
                    fill=qr_color,
                )

            else:
                inner_box = (
                    left + dot_margin,
                    top + dot_margin,
                    right - dot_margin,
                    bottom - dot_margin,
                )

                if dot_style == "Trái tim nhỏ":
                    draw_heart(
                        draw,
                        inner_box,
                        qr_color,
                    )

                else:
                    draw.ellipse(
                        inner_box,
                        fill=qr_color,
                    )

    diameter = int(
        image_size
        * (logo_percent / 100)
    )

    if diameter % 2:
        diameter += 1

    logo_circle = prepare_logo(
        logo_path,
        diameter,
        qr_color,
    )

    position = (
        (image_size - diameter) // 2,
        (image_size - diameter) // 2,
    )

    image.paste(
        logo_circle,
        position,
        logo_circle,
    )

    return image


def image_to_png_bytes(
    image: Image.Image,
) -> bytes:
    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
        optimize=True,
    )

    return buffer.getvalue()


st.set_page_config(
    page_title="Tạo mã QR - IVF Đông Đô",
    page_icon="🔳",
    layout="centered",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 12% 10%,
                    rgba(235, 35, 116, 0.08),
                    transparent 26%
                ),
                radial-gradient(
                    circle at 88% 8%,
                    rgba(23, 44, 116, 0.08),
                    transparent 26%
                ),
                linear-gradient(
                    180deg,
                    #fbfbfe 0%,
                    #ffffff 42%,
                    #fcfbff 100%
                );
        }

        .block-container {
            max-width: 900px;
            padding-top: 0.65rem;
            padding-bottom: 2.5rem;
        }

        .logo-wrap {
            display: flex;
            justify-content: center;
            margin-bottom: 0.55rem;
        }

        div[data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #e8ebf5;
            border-radius: 20px;
            padding: 1.2rem 1.2rem 0.4rem 1.2rem;
            box-shadow: 0 10px 28px rgba(41, 49, 90, 0.07);
        }

        .stButton > button,
        .stDownloadButton > button,
        button[kind="primary"] {
            min-height: 3rem;
            border: 0;
            border-radius: 12px;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .privacy-note {
            text-align: center;
            color: #6b7280;
            font-size: 0.86rem;
            margin-top: 1rem;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if LOGO_PATH.exists():
    st.markdown(
        '<div class="logo-wrap">',
        unsafe_allow_html=True,
    )

    left, center, right = st.columns(
        [1, 1.35, 1]
    )

    with center:
        st.image(
            str(LOGO_PATH),
            width=260,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

else:
    st.warning(
        "Không tìm thấy tệp "
        "logo_ivf_dong_do.png."
    )

with st.form("qr_form"):
    url_input = st.text_input(
        "Đường liên kết cần tạo mã QR",
        placeholder=(
            "Ví dụ: https://docs.google.com/forms/... "
            "hoặc https://www.ivfdongdo.com"
        ),
        help=(
            "Có thể nhập liên kết có hoặc "
            "chưa có phần https://"
        ),
    )

    filename_input = st.text_input(
        "Tên tệp khi tải xuống",
        value="qr_ivf_dong_do",
        help="Không cần nhập đuôi .png",
    )

    col1, col2 = st.columns(2)

    with col1:
        theme_name = st.selectbox(
            "Màu mã QR",
            options=list(
                COLOR_THEMES.keys()
            ),
            index=1,
        )

    with col2:
        quality_label = st.selectbox(
            "Chất lượng ảnh",
            options=list(
                QUALITY_OPTIONS.keys()
            ),
            index=1,
        )

    col3, col4 = st.columns(2)

    with col3:
        dot_style = st.selectbox(
            "Kiểu chấm QR",
            options=DOT_STYLE_OPTIONS,
            index=0,
        )

    with col4:
        logo_percent = st.slider(
            "Kích thước logo (%)",
            min_value=18,
            max_value=28,
            value=24,
            step=1,
        )

    submitted = st.form_submit_button(
        "TẠO MÃ QR",
        type="primary",
        use_container_width=True,
    )

if submitted:
    normalized_url = normalize_url(
        url_input
    )

    if not normalized_url:
        st.error(
            "Vui lòng nhập đường liên kết "
            "cần tạo mã QR."
        )

    elif not is_valid_web_url(
        normalized_url
    ):
        st.error(
            "Đường liên kết chưa hợp lệ. "
            "Vui lòng nhập theo dạng "
            "https://tenmien.vn"
        )

    elif not LOGO_PATH.exists():
        st.error(
            "Không thể tạo mã QR vì chưa có "
            "tệp logo_ivf_dong_do.png."
        )

    else:
        try:
            qr_image = create_branded_qr(
                data=normalized_url,
                logo_path=LOGO_PATH,
                qr_color=hex_to_rgb(
                    COLOR_THEMES[
                        theme_name
                    ]["qr"]
                ),
                box_size=QUALITY_OPTIONS[
                    quality_label
                ],
                logo_percent=logo_percent,
                dot_style=dot_style,
            )

            st.session_state[
                "qr_png"
            ] = image_to_png_bytes(
                qr_image
            )

            st.session_state[
                "qr_filename"
            ] = (
                safe_filename(
                    filename_input
                )
                + ".png"
            )

            st.session_state[
                "qr_url"
            ] = normalized_url

            st.session_state[
                "qr_theme"
            ] = theme_name

            st.session_state[
                "qr_dot_style"
            ] = dot_style

            st.session_state[
                "qr_logo_size"
            ] = logo_percent

            st.success(
                "Đã tạo mã QR thành công."
            )

        except Exception as exc:
            st.error(
                "Không thể tạo mã QR. "
                f"Chi tiết lỗi: {exc}"
            )

if "qr_png" in st.session_state:
    st.subheader(
        "Xem trước mã QR"
    )

    left, center, right = st.columns(
        [1, 3, 1]
    )

    with center:
        st.image(
            st.session_state["qr_png"],
            use_container_width=True,
        )

    st.caption(
        "Liên kết đã mã hóa: "
        f"{st.session_state['qr_url']}  •  "
        "Màu: "
        f"{st.session_state['qr_theme']}  •  "
        "Kiểu chấm: "
        f"{st.session_state['qr_dot_style']}  •  "
        "Logo: "
        f"{st.session_state['qr_logo_size']}%"
    )

    st.download_button(
        label=(
            "TẢI MÃ QR ĐỊNH DẠNG PNG"
        ),
        data=st.session_state["qr_png"],
        file_name=st.session_state[
            "qr_filename"
        ],
        mime="image/png",
        type="primary",
        use_container_width=True,
    )

st.markdown(
    (
        '<div class="privacy-note">'
        "Ứng dụng tạo ảnh trực tiếp "
        "trong phiên làm việc và không lưu "
        "đường liên kết vào cơ sở dữ liệu."
        "</div>"
    ),
    unsafe_allow_html=True,
)
