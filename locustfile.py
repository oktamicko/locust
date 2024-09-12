import csv
import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from locust import HttpUser, task, between, events

# Memuat variabel dari file .env
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

# Variabel untuk menyimpan hasil test
results = []


# TaskSet untuk menjalankan tes Locust
class WebsiteUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")

    wait_time = between(1, 5)


# Fungsi untuk menulis hasil ke file CSV
def write_csv(filename):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Method", "Name", "Response Time", "Number of Requests", "Failure Message"]
        )
        for result in results:
            writer.writerow(result)


# Fungsi untuk mengirim email dengan lampiran CSV
def send_email(subject, body, to_email, filename):
    # Membuat objek email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    # Melampirkan teks email
    msg.attach(MIMEText(body, "plain"))

    # Melampirkan file CSV
    attachment = open(filename, "rb")
    part = MIMEBase("application", "octet-stream")
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
    msg.attach(part)

    try:
        # Menyiapkan koneksi ke server SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Mengaktifkan TLS untuk keamanan
        server.login(EMAIL_USER, EMAIL_PASS)  # Masuk ke server email
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)  # Mengirim email
        server.quit()
        print("Email berhasil dikirim dengan lampiran CSV!")
    except Exception as e:
        print(f"Gagal mengirim email: {e}")


# Event handler untuk mencatat permintaan sukses dan gagal
@events.request.add_listener
def request_listener(
    request_type, name, response_time, response_length, exception, **kwargs
):
    if exception:
        results.append([request_type, name, response_time, 0, str(exception)])
    else:
        results.append([request_type, name, response_time, 1, ""])


# Event handler untuk Locust yang dipanggil setelah semua tes selesai
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Tes selesai, menulis hasil ke CSV dan mengirim email...")

    # Nama file CSV
    csv_filename = "locust_test_results.csv"

    # Menulis hasil tes ke file CSV
    write_csv(csv_filename)

    # Mengirim email dengan lampiran CSV
    subject = "Locust Test Completed with Results"
    body = "The load test has been successfully completed. Attached is the CSV file containing the test results."
    send_email(subject, body, RECIPIENT_EMAIL, csv_filename)

    # Menghapus file CSV setelah dikirim
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        print("File CSV dihapus setelah pengiriman email. ")
