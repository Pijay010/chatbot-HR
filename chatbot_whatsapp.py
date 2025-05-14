from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd
from nltk.tokenize import word_tokenize
import re

app = Flask(__name__)
karyawan = pd.read_csv('dataset_chatbot_updated.csv', sep=';', encoding='utf-8')
pertanyaan = pd.read_csv('dataset_pertanyaan_chatbot.csv', sep=';', encoding='utf-8')
first_attempt = {}

def chatbot_response(id_karyawan, question):
    print(f"Processing ID: {id_karyawan}, Question: {question}")
    employee = karyawan[karyawan["ID_Karyawan"] == id_karyawan]
    if employee.empty:
        return "ID tidak ditemukan"
    sisa_cuti = employee["Jatah_Cuti"].iloc[0] - employee["Cuti_Terpakai"].iloc[0]
    riwayat = employee["Riwayat_Pengajuan_Cuti"].iloc[0]
    tokens = word_tokenize(question.lower())
    for _, row in pertanyaan.iterrows():
        if row["Pertanyaan"].lower() in question.lower() or all(word in tokens for word in row["Pertanyaan"].lower().split()):
            jawaban = row["Jawaban"]
            return jawaban.replace("[ID_Karyawan]", str(id_karyawan)).replace("[Sisa_Cuti]", str(sisa_cuti)).replace("[Riwayat_Pengajuan]", riwayat)
    if "cuti" in tokens and any(x in tokens for x in ["sisa", "berapa", "tinggal"]):
        return f"Halo id {id_karyawan}, sisa cuti Anda: {sisa_cuti} hari"
    elif "cuti" in tokens and any(x in tokens for x in ["kapan", "terakhir", "riwayat"]):
        return f"Halo id {id_karyawan}, riwayat cuti Anda: {riwayat}"
    elif "gajian" in tokens or "gaji" in tokens:
        return f"Halo id {id_karyawan}, gajian tanggal 1"
    return f"Halo id {id_karyawan}, maaf, pertanyaan tidak dikenali"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    data = request.json
    incoming_msg = data.get("text", "").strip()
    from_number = data.get("waId", "")
    print(f"Received message: {incoming_msg} from {from_number}")
    resp = {"text": ""}
    is_first = first_attempt.get(from_number, True)
    try:
        cleaned_msg = re.sub(r'[^0-9a-zA-Z\s?]', '', incoming_msg.replace("id", "").lower()).strip()
        parts = cleaned_msg.split(" ", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            raise ValueError("Invalid format")
        id_karyawan = int(parts[0])
        question = parts[1]
        response = chatbot_response(id_karyawan, question)
        first_attempt[from_number] = False
    except Exception as e:
        print(f"Error: {e}")
        if is_first:
            response = ("Upps! format pertanyaan yang kamu buat salah! "
                       "Silahkan ikuti format sebagai berikut 'ID [3 digit], Pertanyaan?'. "
                       "Kamu bisa memilih pertanyaan sesuai dengan kebutuhan: "
                       "1. Cuti (Contoh: Berapa sisa cuti saya?) "
                       "2. Riwayat pengajuan cuti (Contoh: Kapan saya terakhir cuti?) "
                       "3. Gaji (Contoh: Kenapa gaji saya belum masuk?) "
                       "4. Kebijakan (Contoh: Kapan bisa WFH?)")
            first_attempt[from_number] = False
        else:
            response = "Format salah. Kirim: ID Pertanyaan (contoh: 448 Berapa sisa cuti saya?)"
    resp["text"] = response
    return resp
if __name__ == "__main__":
    app.run(debug=True, port=5000)
