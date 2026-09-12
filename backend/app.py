from flask import Flask, request, jsonify, send_from_directory, session
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import os
import uuid
import shutil
from pathlib import Path
import requests
import google.generativeai as genai
from dotenv import load_dotenv
# Moduls
from config import create_app, folder_setup, database_connection, model_setup
from generate_table import create_users_table, create_predict_result_table
from auth import login, register, logout, current_user  
from my_profile import get_my_profile, update_my_profile
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import re


app = Flask(__name__)
load_dotenv()

FONNTE_API_KEY = os.getenv("FONNTE_API_KEY")

# Konfigurasi Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY belum di-set. Cek file .env atau environment variable.")

genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel("gemini-2.5-flash")


# Calling config functions
app = create_app()
UPLOAD_FOLDER, PDF_FOLDER = folder_setup()
db = database_connection();
model_acne_detection, model_skin_type = model_setup()


# Generate table
def generate_all_tables():
    create_users_table()
    create_predict_result_table()



def hitung_keparahan(jumlah):
    if jumlah <= 5:
        return "Ringan"
    elif jumlah <= 13:
        return "Sedang"
    else:
        return "Berat"
    


def generate_ai_summary_analysis(total_acne, severity_level, skin_type, skin_confidence):
    """
    Panggil Gemini untuk bikin analisa dan saran perawatan singkat.
    Kalau error, fallback ke analisa default.
    """

    # skin_confidence dari YOLO biasanya 0–1
    # Kalau kamu nanti kirim ke frontend dalam persen, itu beda variabel
    confidence_percent = round(float(skin_confidence) * 100, 1)

    prompt = f"""
    Ibaratkan anda adalah s3 dokter spesialis kulit yang lulusan dari 
    universitas nomor 1 terbaik di dunia dengan lulus cumlaude selalu 
    mendapatkan ipk 3.9 selalu tulis jurnal scopus minimal 4 jurnal per 3 bulan, 
    hampir setiap seminggu sekali anda sebagai dokter selalu melakukan operasi kulit 
    wajah manusia Berdasarkan hasil deteksi berikut:

    - Total Acne: {total_acne}
    - Severity Level: {severity_level}
    - Skin Type: {skin_type}
    - Skin Confidence: {confidence_percent}%

    Tulis jawaban dalam bahasa Indonesia yang:
    - Mudah dipahami orang awam.
    - Jelaskan kondisi kulit secara singkat (misalnya apakah termasuk ringan/sedang/berat dan apa artinya).
    - Tuliskan point-point penting dari hasil deteksi.
    - Bold seperti Jumlah Jerawat, Tingkat Keparahan, dan Tipe Kulit dalam jawabanmu.
    - Tambahkan 1 kalimat disclaimer bahwa ini bukan pengganti konsultasi langsung dengan dokter.
    - Jawaban wajib mutlak sempurna, sepenuhnya benar, dan tanpa kesalahan atau keburukan sedikitpun. Kualitas jawaban harus yang terbaik, tak tertandingi.
    - Jawab langsung ke intinya, tidak perlu dan jangan menceritakan latar belakang anda hanya jawaban inti dari seluruh pertanyaan di percakapan ini
    - Jangan beri kata kata yang menanyakan keadaan atau lalu jawaban. "Apa artinya tingkat keparahan begini?" Langsung penjelasan jawaban saja
    """

    try:
        response = gemini_model.generate_content(prompt)
        print("Gemini response object:", response)  # DEBUG
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Response Gemini kosong")
        return text
    except Exception as e:
        # DI SINI KITA TAMPILKAN ERRORNYA DI LOG
        print("Error Gemini saat generate analisa:", repr(e))

        # fallback ke analisa default (ini yg sekarang kamu lihat di UI)
        return (
            f"Terdeteksi {total_acne} jerawat. "
            f"Tingkat keparahan dikategorikan sebagai '{severity_level}'. "
            f"Tipe kulit terdeteksi: {skin_type}."
        )

def generate_ai_recommendation_analysis(total_acne, severity_level, skin_type, skin_confidence):
    """
    Panggil Gemini untuk bikin analisa dan saran perawatan singkat.
    Kalau error, fallback ke analisa default.
    """

    # skin_confidence dari YOLO biasanya 0–1
    # Kalau kamu nanti kirim ke frontend dalam persen, itu beda variabel
    confidence_percent = round(float(skin_confidence) * 100, 1)

    prompt = f"""
    Ibaratkan anda adalah s3 dokter spesialis kulit yang lulusan dari 
    universitas nomor 1 terbaik di dunia dengan lulus cumlaude selalu 
    mendapatkan ipk 3.9 selalu tulis jurnal scopus minimal 4 jurnal per 3 bulan, 
    hampir setiap seminggu sekali anda sebagai dokter selalu melakukan operasi kulit 
    wajah manusia Berdasarkan hasil deteksi berikut:

    - Total Acne: {total_acne}
    - Severity Level: {severity_level}
    - Skin Type: {skin_type}
    - Skin Confidence: {confidence_percent}%

    Tulis jawaban dalam bahasa Indonesia yang:
    - Mudah dipahami orang awam.
    - Ringkas saran perawatan harian yang sesuai dengan tipe kulit dan tingkat keparahan jerawat.
    - Gunakan format poin-poin untuk saran perawatan.
    - Berikan saran dasar perawatan harian yang aman dan umum (tanpa menyebut merek/obat spesifik).
    - Tambahkan 1 kalimat disclaimer bahwa ini bukan pengganti konsultasi langsung dengan dokter.
    - Jawaban wajib mutlak sempurna, sepenuhnya benar, dan tanpa kesalahan atau keburukan sedikitpun. Kualitas jawaban harus yang terbaik, tak tertandingi.
    - Jawab langsung ke intinya, tidak perlu dan jangan menceritakan latar belakang anda hanya jawaban inti dari seluruh pertanyaan di percakapan ini
    - Jangan beri kata kata yang menanyakan keadaan atau lalu jawaban. seperti kata "Penanganan apa untuk menyelesaikan kondisi begini?" Langsung penjelasan jawaban saja
    """

    try:
        response = gemini_model.generate_content(prompt)
        print("Gemini response object:", response)  # DEBUG
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Response Gemini kosong")
        return text
    except Exception as e:
        # DI SINI KITA TAMPILKAN ERRORNYA DI LOG
        print("Error Gemini saat generate analisa:", repr(e))

        # fallback ke analisa default (ini yg sekarang kamu lihat di UI)
        return (
            f"Terdeteksi {total_acne} jerawat. "
            f"Tingkat keparahan dikategorikan sebagai '{severity_level}'. "
            f"Tipe kulit terdeteksi: {skin_type}."
        )

def build_whatsapp_message(result: dict) -> str:
    """
    Bangun template pesan WhatsApp untuk hasil Acne Detection + Gemini.
    `result` diambil dari jerawatAnalysis (response /predict).
    """
    total_acne = result.get("jumlah_jerawat", 0)
    severity = result.get("tingkat_keparahan", "-")
    skin_type = result.get("tipe_kulit", "Tidak terdeteksi")
    skin_conf = result.get("skin_confidence", 0)  # sudah dalam persen
    summary = result.get("analisa_summary", "")
    recommendation = result.get("analisa_recommendation", "")
    if not summary and not recommendation:
        combined_analysis = result.get("analisa", "-")
    else:
        combined_analysis = f"hasil ringkasan:\n{summary}\nrekomendasi penanganan:\n{recommendation}"

    message = f"""
Acne Detection Result

Total Acne : {total_acne}
Severity   : {severity}
Skin Type  : {skin_type}
Confidence : {skin_conf:.1f}%

AI Analysis & Recommendation:
{combined_analysis}

Catatan:
Hasil ini dibuat secara otomatis oleh sistem deteksi jerawat dan AI (Gemini).
Saran ini bersifat umum dan tidak menggantikan konsultasi langsung dengan dokter kulit.
""".strip()

    return message


def send_whatsapp_fonnte(phone_number: str, message: str):
    """
    Kirim pesan WhatsApp menggunakan Fonnte.
    phone_number harus format internasional tanpa +, contoh: 6281234567890
    Return: (success: bool, detail: dict/str)
    """
    if not FONNTE_API_KEY:
        print("FONNTE_API_KEY belum di-set")
        return False, {"error": "API key not set"}

    url = "https://api.fonnte.com/send"

    payload = {
        "target": phone_number,
        "message": message,
    }

    headers = {
        "Authorization": FONNTE_API_KEY,
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=20)
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}

        print("Fonnte status:", resp.status_code, "response:", data)

        # aturan sukses bisa disesuaikan dengan format resmi Fonnte
        success = resp.status_code == 200 and bool(data)

        return success, data
    except Exception as e:
        print("Error kirim WhatsApp via Fonnte:", e)
        return False, {"error": str(e)}


@app.route("/send-to-wa", methods=["POST"])
def send_to_wa():
    """
    Body JSON yang diharapkan:
    {
      "phone": "6281234567890",
      "result": { ...isi dari jerawatAnalysis... }
    }
    """
    try:
        data = request.get_json() or {}
        phone = data.get("phone")
        result = data.get("result") or {}

        if not phone:
            return jsonify({"success": False, "message": "phone wajib diisi"}), 400

        # Bangun pesan dari result (jerawatAnalysis)
        phone = phone.replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = "62" + phone[1:]
        message = build_whatsapp_message(result)

        success, detail = send_whatsapp_fonnte(phone, message)

        return jsonify({
            "success": success,
            "detail": detail,
        }), 200 if success else 500

    except Exception as e:
        print("Error di /send-to-wa:", e)
        return jsonify({"success": False, "error": str(e)}), 500



@app.route("/test-fonnte", methods=["GET"])
def test_fonnte():
    phone = request.args.get("phone")  # contoh: ?phone=6281234567890
    if not phone:
        return jsonify({"success": False, "message": "Tambahkan ?phone=628xxxx"}), 400

    success, detail = send_whatsapp_fonnte(phone, "Tes kirim WA dari backend Flask ✅")

    return jsonify({
        "success": success,
        "detail": detail,
    }), 200 if success else 500



def prediksi_tipe_kulit(image_path: str):
    """
    Jalankan model skin-type dan kembalikan nama kelas + confidence.
    Kalau gagal, balikin (None, None) supaya tidak bikin error 500.
    """
    try:
        results = model_skin_type.predict(source=image_path, save=False, conf=0.2)
        if not results:
            return None, None

        r = results[0]

        # Model klasifikasi YOLO (probs)
        if hasattr(r, "probs") and r.probs is not None:
            class_id = int(r.probs.top1)
            class_name = r.names[class_id]
            confidence = float(r.probs.top1conf)
            return class_name, confidence

        # Fallback kalau bukan klasifikasi
        return None, None
    except Exception as e:
        print("Error prediksi tipe kulit:", e)
        return None, None


def generate_pdf(pdf_path, image_path, jumlah, keparahan, summary, recommendation, tipe_kulit=None):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    style_body = styles["BodyText"]
    style_bold = styles["Heading3"]
    style_body.allowWidows = 0
    style_body.allowOrphans = 0
    
    # FUNGSI PEMBERSIH FORMAT (MD -> ReportLab XML)
    def clean_format(text):
        if not text: return ""
        text = str(text)
        # 1. Ganti **text** menjadi <b>text</b> (Bold)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # 2. Ganti * bullet menjadi bullet point visual
        text = text.replace("* ", "<br/>• ")
        # 3. Ganti newline (\n) menjadi <br/> agar turun baris
        text = text.replace("\n", "<br/>")
        return text

    # Bersihkan teks sebelum dicetak
    summary_clean = clean_format(summary)
    recommendation_clean = clean_format(recommendation)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Laporan Deteksi Jerawat")
    img_height_allocated = 0
    # Gambar
    if os.path.exists(image_path):
        try:
            img_width = 400
            img_height_target = 300
            y_img = height - 100 - img_height_target
            c.drawImage(
                image_path,
                50,
                y_img,
                width=img_width,
                height=img_height_target,
                preserveAspectRatio=True,
            )
            img_height_allocated = img_height_target

        except Exception as e:
            print(f"Error menggambar gambar ke PDF: {e}")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 320, "Gambar tidak dapat dimuat di PDF.")
            img_height_allocated = 50
    else:
        img_height_allocated = 0

    y = height - 100 - img_height_allocated - 40
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Jumlah Jerawat: {jumlah}")
    y -= 20
    c.drawString(50, y, f"Tingkat Keparahan: {keparahan}")
    y -= 20
    if tipe_kulit:
        c.drawString(50, y, f"Tipe Kulit: {tipe_kulit}")
        y -= 20
    y -= 30
    text_width = width - 100
    # Menampilkan AI Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Ringkasan AI:")
    y -= 15 # Turun sedikit untuk isi teks
    p_summary = Paragraph(summary_clean, style_body)
    w, h = p_summary.wrap(text_width, height)
    p_summary.drawOn(c, 50, y - h)
    y -= (h + 20) # h adalah tinggi teks, 20 adalah gap antar section
    if y < 100:
        c.showPage() # Buat halaman baru jika penuh
        y = height - 50 # Reset y ke atas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Rekomendasi AI:")
    y -= 15
    p_rec = Paragraph(recommendation_clean, style_body)
    w, h = p_rec.wrap(text_width, height)
    p_rec.drawOn(c, 50, y - h)

    c.showPage()
    c.save()
    print(f"PDF Berhasil dibuat di: {pdf_path}")
    
@app.route("/test-gemini", methods=["GET"])
def test_gemini():
    try:
        res = gemini_model.generate_content(
            "Tulis satu kalimat pendek dalam bahasa Indonesia tentang pentingnya merawat kulit wajah."
        )
        return jsonify({
            "ok": True,
            "text": res.text.strip()
        })
    except Exception as e:
        print("Error /test-gemini:", repr(e))
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500



@app.route('/predict', methods=['POST'])
def predict():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Unauthorized. Please login first."
            }), 401

        file = request.files['image']
        image = Image.open(io.BytesIO(file.read()))

        # Simpan gambar input sementara
        image_filename = f"{uuid.uuid4().hex}.jpg"
        input_path = os.path.join(UPLOAD_FOLDER, image_filename)
        image.save(input_path)

        # ===== 1. Prediksi jerawat =====
        results = model_acne_detection.predict(source=input_path, save=True, conf=0.2)
        jumlah_jerawat = len(results[0].boxes) if results and results[0].boxes is not None else 0
        tingkat_keparahan = hitung_keparahan(jumlah_jerawat)

        # ===== 2. Prediksi tipe kulit =====
        tipe_kulit, skin_conf = prediksi_tipe_kulit(input_path)
        if tipe_kulit is None:
            tipe_kulit = "Tidak terdeteksi"
            skin_conf = 0.0

        # ===== 3. Panggil Gemini untuk analisa =====
        analisa_text_ai_summary = generate_ai_summary_analysis(
            total_acne=jumlah_jerawat,
            severity_level=tingkat_keparahan,
            skin_type=tipe_kulit,
            skin_confidence=skin_conf,
        )

        analisa_text_ai_recommendation = generate_ai_recommendation_analysis(
            total_acne=jumlah_jerawat,
            severity_level=tingkat_keparahan,
            skin_type=tipe_kulit,
            skin_confidence=skin_conf,
        )

        # ===== 4. Simpan gambar hasil YOLO =====
        result_dir = Path(results[0].save_dir)
        result_img_path = result_dir / image_filename
        final_filename = f"pred_{image_filename}"
        final_path = os.path.join(UPLOAD_FOLDER, final_filename)
        shutil.copy(result_img_path, final_path)

        # ===== 5. Simpan ke database =====
        cursor = db.cursor()
        sql = """
            INSERT INTO predict_result 
                (user_id, file_name, acne_count, severity, skin_type, skin_confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        val = (
            user_id,
            final_filename,
            jumlah_jerawat,
            tingkat_keparahan,
            tipe_kulit,
            skin_conf,
        )
        cursor.execute(sql, val)
        db.commit()

        # ===== 6. Generate PDF =====
        pdf_filename = final_filename.replace(".jpg", ".pdf")
        pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
        generate_pdf(
            pdf_path, 
            final_path, 
            jumlah_jerawat, 
            tingkat_keparahan, 
            analisa_text_ai_summary,       # Masuk ke param 'summary'
            analisa_text_ai_recommendation, # Masuk ke param 'recommendation'
            tipe_kulit                     # Masuk ke param 'tipe_kulit'
        )

        return jsonify({
            "image_url": f"http://localhost:5000/results/images/{final_filename}",
            "jumlah_jerawat": jumlah_jerawat,
            "tingkat_keparahan": tingkat_keparahan,
            "analisa_summary": analisa_text_ai_summary,
            "analisa_recommendation": analisa_text_ai_recommendation,
            "tipe_kulit": tipe_kulit,
            "skin_confidence": round(float(skin_conf) * 100, 1),
            "pdf_url": f"http://localhost:5000/download-pdf/{pdf_filename}",
        }), 200

    except Exception as e:
        print("Error di /predict:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/download-pdf/<filename>', methods=['GET'])
def download_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)


@app.route('/results/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/register", methods=["POST"])
def register_route():
    return register(db)


@app.route("/login", methods=["POST"])
def login_route():
    return login(db)


@app.route("/logout", methods=["POST"])
def logout_route():
    return logout()

@app.route("/profile", methods=["GET"])
def my_profile_route():
    return get_my_profile(db)


@app.route("/profile", methods=["PUT", "PATCH"])
def update_profile_route():
    return update_my_profile(db)


@app.route("/history", methods=["GET"])
def history_route():
    # pastikan user sudah login
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "message": "Unauthorized. Please login first."
        }), 401

    cursor = db.cursor(dictionary=True)
    
    # ===== PERBAIKAN DI SINI (Menambahkan skin_type) =====
    cursor.execute("""
        SELECT id, file_name, acne_count, severity, skin_type, created_at
        FROM predict_result
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    # =====================================================
    
    rows = cursor.fetchall()

    history = []
    for row in rows:
        file_name = row["file_name"]

        # bikin nama file PDF dari nama file gambar
        if "." in file_name:
            base = file_name.rsplit(".", 1)[0]
        else:
            base = file_name
        pdf_filename = f"{base}.pdf"

        # analisa sama seperti di /predict
        analisa_text_ai_summary = (
            f"Terdeteksi {row['acne_count']} jerawat. "
            f"Tingkat keparahan dikategorikan sebagai '{row['severity']}'."
        )
        
        # Sekarang baris ini AMAN karena skin_type sudah ada
        analisa_text_ai_recommendation = (
            f"Saran perawatan difokuskan untuk jenis kulit {row['skin_type']} "
            f"guna menangani kondisi jerawat dengan tingkat {row['severity']}."
        )

        history.append({
            "id": row["id"],
            "waktu": row["created_at"].strftime("%Y-%m-%d %H:%M"),
            "jumlah_jerawat": row["acne_count"],
            "tingkat_keparahan": row["severity"],
            "jenis_kulit": row["skin_type"],
            
            # Saran: Gunakan underscore agar sinkron dengan frontend (opsional tapi disarankan)
            "analisa_summary": analisa_text_ai_summary, 
            "analisa_recommendation": analisa_text_ai_recommendation,
            "pdf_url": f"http://localhost:5000/download-pdf/{pdf_filename}",
        })

    return jsonify(history), 200


@app.route("/me", methods=["GET"])
def me_route():
    return current_user(db)


# Generate tables
@app.route("/generate", methods=["GET"])
def generate():
    try:
        generate_all_tables()
        return jsonify({
            "success": True,
            "message": "Tabel users dan predict_result berhasil dibuat (atau sudah ada)."
        }), 200
    except Exception as e:
        print("Error generate table:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/debug-session")
def debug_session():
    print("session sekarang:", dict(session))
    return jsonify({
        "session": dict(session)
    })
    
# auth.py
def current_user(db):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, phone FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],  # <- penting
        }
    })


# Test API
@app.route('/test', methods=['GET'])
def test():
    return "API is working!"


if __name__ == '__main__':
    app.run(debug=True)
