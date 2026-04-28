"""
LPN Generator — Streamlit Web App
Generates unique 10-digit License Plate Numbers and renders 4x6 thermal labels as a downloadable PDF.

Persistence: Supabase (Postgres) — every issued LPN is stored with a UNIQUE constraint so duplicates are impossible.
Auth: shared password via Streamlit secrets.
"""

import os
import random
from datetime import datetime
from io import BytesIO

import streamlit as st
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from supabase import create_client, Client


# ---------------------------- Config ----------------------------
SERIAL_LEN = 9
TOTAL_LEN = 10
LARGE_TAIL = 3
LABEL_W = 6.0 * inch
LABEL_H = 4.0 * inch
PAGE_SIZE = (LABEL_W, LABEL_H)
MAX_RETRIES_PER_LPN = 25  # collision retries per LPN before giving up


# ---------------------------- Auth gate ----------------------------
st.set_page_config(page_title="LPN Generator", page_icon="🏷️", layout="centered")

def _password_gate() -> bool:
    expected = st.secrets.get("app_password", "")
    if not expected:
        st.error("App is misconfigured: `app_password` is not set in Streamlit secrets.")
        st.stop()
    if st.session_state.get("authed"):
        return True
    st.markdown("### LPN Generator")
    pw = st.text_input("Password", type="password", key="pw_input")
    if st.button("Enter"):
        if pw == expected:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

_password_gate()


# ---------------------------- Supabase ----------------------------
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets.get("supabase_url", "")
    key = st.secrets.get("supabase_key", "")
    if not url or not key:
        st.error("Supabase secrets are missing. Set `supabase_url` and `supabase_key` in Streamlit secrets.")
        st.stop()
    return create_client(url, key)


sb = get_supabase()


# ---------------------------- LPN math ----------------------------
def mod10_check_digit(digits: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return str((10 - (total % 10)) % 10)


def generate_unique_lpn(client_name: str) -> str:
    """
    Generate one new 10-digit LPN (9 random + check digit) and insert into Supabase.
    Relies on the UNIQUE constraint on lpns.lpn — retries on collision.
    """
    for _ in range(MAX_RETRIES_PER_LPN):
        serial = "".join(str(random.randint(0, 9)) for _ in range(SERIAL_LEN))
        lpn = serial + mod10_check_digit(serial)
        try:
            sb.table("lpns").insert({"lpn": lpn, "client": client_name}).execute()
            return lpn
        except Exception as e:
            msg = str(e).lower()
            # 23505 = unique_violation in Postgres; the supabase-py error wrapping varies, so match loosely
            if "duplicate" in msg or "unique" in msg or "23505" in msg:
                continue
            raise
    raise RuntimeError("Could not generate a unique LPN after many attempts.")


# ---------------------------- Barcode ----------------------------
def make_barcode_png(lpn: str) -> ImageReader:
    code128 = barcode.get("code128", lpn, writer=ImageWriter())
    buf = BytesIO()
    code128.write(
        buf,
        options={
            "module_width": 0.4,
            "module_height": 18.0,
            "quiet_zone": 2.0,
            "write_text": False,
            "background": "white",
            "foreground": "black",
            "dpi": 300,
        },
    )
    buf.seek(0)
    return ImageReader(buf)


# ---------------------------- Label drawing ----------------------------
def draw_label(c: canvas.Canvas, lpn: str, client_name: str, date_str: str) -> None:
    margin = 0.20 * inch
    inner_w = LABEL_W - 2 * margin

    # Header
    header_y = LABEL_H - margin - 0.18 * inch
    c.setFont("Helvetica", 12)
    c.drawString(margin, header_y, f"Client: {client_name}")
    c.drawRightString(LABEL_W - margin, header_y, f"Date: {date_str}")

    # Big LPN with last 3 digits larger
    head = lpn[: TOTAL_LEN - LARGE_TAIL]
    tail = lpn[-LARGE_TAIL:]
    head_size, tail_size = 44, 60
    head_w = c.stringWidth(head, "Helvetica-Bold", head_size)
    tail_w = c.stringWidth(tail, "Helvetica-Bold", tail_size)
    total_w = head_w + tail_w
    big_y = LABEL_H - 1.55 * inch
    start_x = (LABEL_W - total_w) / 2.0
    c.setFont("Helvetica-Bold", head_size)
    c.drawString(start_x, big_y, head)
    c.setFont("Helvetica-Bold", tail_size)
    c.drawString(start_x + head_w, big_y, tail)

    # Barcode
    barcode_img = make_barcode_png(lpn)
    c.drawImage(
        barcode_img, margin, 0.45 * inch, width=inner_w, height=0.95 * inch,
        preserveAspectRatio=False, mask="auto",
    )

    # Human-readable LPN under barcode
    c.setFont("Helvetica", 12)
    c.drawCentredString(LABEL_W / 2.0, 0.20 * inch, lpn)


def build_pdf(lpns: list[str], client_name: str, date_str: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=PAGE_SIZE)
    for lpn in lpns:
        draw_label(c, lpn, client_name, date_str)
        c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------- UI ----------------------------
st.title("🏷️ LPN Generator")
st.caption("Generate unique License Plate Numbers as 4×6 thermal labels (Rollo).")

with st.form("gen_form"):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Client", value="Nominal Jewelry")
    with col2:
        date_str = st.text_input("Date (MM/DD/YY)", value=datetime.now().strftime("%m/%d/%y"))
    count = st.number_input("How many labels?", min_value=1, max_value=500, value=10, step=1)
    submitted = st.form_submit_button("Generate")

if submitted:
    if not client_name.strip():
        st.error("Client name is required.")
    else:
        progress = st.progress(0.0, text="Generating LPNs…")
        new_lpns = []
        try:
            for i in range(int(count)):
                new_lpns.append(generate_unique_lpn(client_name.strip()))
                progress.progress((i + 1) / count, text=f"Generated {i+1}/{count}")
            progress.empty()

            pdf_bytes = build_pdf(new_lpns, client_name.strip(), date_str.strip())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lpns_{ts}_{count}.pdf"

            st.success(f"Generated {len(new_lpns)} unique LPN(s).")
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                type="primary",
            )

            with st.expander("Show LPN list"):
                st.code("\n".join(new_lpns))

        except Exception as e:
            progress.empty()
            st.error(f"Failed: {e}")

# Footer with stats
try:
    total = sb.table("lpns").select("id", count="exact").execute()
    st.caption(f"Total LPNs ever issued: **{total.count}**")
except Exception:
    pass
