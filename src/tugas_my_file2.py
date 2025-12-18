# kode aplikasi analisis iklim dengan GUI menggunakan customtkinter (Pemdas)

# library 
import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
from reportlab.lib.enums import TA_CENTER


# helpers
def load_data_csv(file="data_iklim.txt"):
    """Load CSV and ensure expected columns exist. Returns a DataFrame with index=Bulan."""
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise FileNotFoundError(f"Gagal membuka file '{file}': {e}")

    # validasi data
    required = {"Bulan", "Suhu_Rata", "Suhu_Max", "Suhu_Min", "Curah_Hujan"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"File CSV harus berisi kolom: {required}. Ditemukan: {list(df.columns)}")

    df = df.copy()
    
    # pastikan 'bulan' adalah string dan set sebagai index
    df["Bulan"] = df["Bulan"].astype(str)
    df.set_index("Bulan", inplace=True)

    # ubah kolom numerik
    for c in ["Suhu_Rata", "Suhu_Max", "Suhu_Min", "Curah_Hujan"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# load data awal
try:
    data = load_data_csv()
except Exception as e:
    # membuat data dummy jika gagal memuat data asli
    print("Peringatan saat memuat data:", e)
    data = pd.DataFrame({
        "Suhu_Rata": [0],
        "Suhu_Max": [0],
        "Suhu_Min": [0],
        "Curah_Hujan": [0]
    }, index=["-"])


# APLIKASI UTAMA
class ClimateApp:
    def __init__(self, master=None):
        self.root = ctk.CTk() if master is None else master
        self.root.title("Aplikasi Analisis Iklim Surabaya")
        self.root.geometry("1200x800")
        self.root.configure(fg_color="#f5f7fa")

        # menyimpan referensi ke kanvas matplotlib
        self.canvas = None

        self.setup_ui()

    def setup_ui(self):
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # header
        header_frame = ctk.CTkFrame(main_container, fg_color="#2c3e50", corner_radius=10, height=100)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text="ANALISIS IKLIM SURABAYA",
            font=("Segoe UI", 28, "bold"),
            text_color="white"
        )
        title_label.pack(pady=25)

        # quick stats
        stats_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=12)
        stats_frame.pack(fill="x", pady=(0, 20))

        overview_title = ctk.CTkLabel(
            stats_frame,
            text="OVERVIEW",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50"
        )
        overview_title.pack(anchor="w", padx=20, pady=10)

        stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_container.pack(fill="x", padx=20, pady=10)

        # data statistik ringkas
        try:
            avg_year = data["Suhu_Rata"].mean()
            max_year = data["Suhu_Max"].max()
            min_year = data["Suhu_Min"].min()
            rain_sum = data["Curah_Hujan"].sum()
        except Exception:
            avg_year = max_year = min_year = rain_sum = 0

        stats_data = [
            {"title": "SUHU RATA-RATA", "value": f"{avg_year:.1f}°C", "color": "#3498db"},
            {"title": "SUHU TERTINGGI", "value": f"{max_year:.1f}°C", "color": "#e74c3c"},
            {"title": "SUHU TERENDAH", "value": f"{min_year:.1f}°C", "color": "#2ecc71"},
            {"title": "CURAH HUJAN", "value": f"{rain_sum:.0f} mm", "color": "#9b59b6"}
        ]

        for stat in stats_data:
            card = ctk.CTkFrame(stats_container, fg_color="#f8f9fa", corner_radius=8,
                                border_width=1, border_color="#e9ecef")
            card.pack(side="left", expand=True, fill="both", padx=10)

            ctk.CTkLabel(card, text=stat["value"], font=("Segoe UI", 24, "bold"),
                         text_color=stat["color"]).pack(anchor="w", padx=15, pady=(10, 0))
            ctk.CTkLabel(card, text=stat["title"], font=("Segoe UI", 12),
                         text_color="#6c757d").pack(anchor="w", padx=15)

        # main content
        content_container = ctk.CTkFrame(main_container, fg_color="transparent")
        content_container.pack(fill="both", expand=True)

        # left side
        left_frame = ctk.CTkFrame(content_container, fg_color="white", corner_radius=12)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(left_frame, text="KONTROL ANALISIS",
                     font=("Segoe UI", 16, "bold"), text_color="#2c3e50").pack(
                     anchor="w", padx=20, pady=20)

        # pilih bulan menggunakan CTkOptionMenu 
        month_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        month_container.pack(fill="x", padx=20)

        ctk.CTkLabel(month_container, text="Pilih Bulan:",
                     font=("Segoe UI", 14), text_color="#495057").pack(side="left")

        months = list(data.index)
        if not months:
            months = ["-"]

        self.month_var = ctk.StringVar(value=months[0])
        self.month_menu = ctk.CTkOptionMenu(month_container, values=months, variable=self.month_var, width=200)
        self.month_menu.pack(side="left", padx=10)

        # actions buttons
        btn_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_container.pack(fill="x", padx=20, pady=10)

        self.analyze_btn = ctk.CTkButton(
            btn_container, text="Analisis Detail",
            command=self.show_analysis,
            fg_color="#3498db", width=150)
        self.analyze_btn.pack(side="left", padx=5)

        self.pdf_btn = ctk.CTkButton(
            btn_container, text="Export PDF",
            command=self.export_pdf,
            fg_color="#27ae60", width=150)
        self.pdf_btn.pack(side="left", padx=5)

        # texbox hasil analisis
        ctk.CTkLabel(left_frame, text="HASIL ANALISIS",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").pack(anchor="w", padx=20, pady=10)

        # CTkTextbox dengan teks warna hitam
        self.analysis_text = ctk.CTkTextbox(
            left_frame, 
            width=520, 
            height=320, 
            fg_color="#f8f9fa",
            border_width=1, 
            border_color="#e9ecef",
            text_color="black"  
        )
        self.analysis_text.pack(fill="both", expand=False, padx=20, pady=20)

        self.show_welcome()

        # right side
        right_frame = ctk.CTkFrame(content_container, fg_color="white", corner_radius=12)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(right_frame, text="VISUALISASI DATA",
                     font=("Segoe UI", 16, "bold"),
                     text_color="#2c3e50").pack(anchor="w", padx=20, pady=20)

        chart_btn_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        chart_btn_container.pack(fill="x", padx=20)

        ctk.CTkButton(chart_btn_container, text="🌡️ Grafik Suhu",
                      command=self.chart_temp,
                      fg_color="#e74c3c", width=160).pack(side="left", padx=10)

        ctk.CTkButton(chart_btn_container, text="💧 Grafik Hujan",
                      command=self.chart_rain,
                      fg_color="#9b59b6", width=160).pack(side="left")

        # area kanvas matplotlib
        self.plot_area = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.plot_area.pack(fill="both", expand=True, padx=20, pady=20)

    
    # welcome text
    def show_welcome(self):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "Selamat datang! Pilih bulan dan mulai analisis.")
        self.analysis_text.configure(state="disabled")

    
    # analisis iklim per bulan
    def show_analysis(self):
        m = self.month_var.get()
        if m not in data.index:
            self._set_analysis_text("Data untuk bulan yang dipilih tidak tersedia.")
            return

        row = data.loc[m]
        avg, mx, mn, r = row["Suhu_Rata"], row["Suhu_Max"], row["Suhu_Min"], row["Curah_Hujan"]

        if pd.isna(r):
            season = "Data curah hujan tidak tersedia"
        else:
            if r > 150:
                season = "Musim Hujan "
            elif r < 50:
                season = "Musim Kemarau "
            else:
                season = "Musim Peralihan "

        text = f"""
 ANALISIS IKLIM BULAN {m.upper()}

 Suhu Rata-rata : {avg}°C
 Suhu Maksimum  : {mx}°C
 Suhu Minimum   : {mn}°C

 Curah Hujan     : {r} mm
 Musim           : {season}
"""

        self._set_analysis_text(text)

    def _set_analysis_text(self, text: str):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", text)
        self.analysis_text.configure(state="disabled")

    
    # grafik suhu (tertanam)
    def _clear_canvas(self):
        if self.canvas:
            try:
                self.canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.canvas = None

    def chart_temp(self):
        months = list(data.index)
        avg = data["Suhu_Rata"].values
        mx = data["Suhu_Max"].values
        mn = data["Suhu_Min"].values

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(months, avg, marker='o', label="Rata-rata")
        ax.plot(months, mx, marker='s', label="Maksimum")
        ax.plot(months, mn, marker='^', label="Minimum")
        ax.set_xticklabels(months, rotation=45)
        ax.set_ylabel("Suhu (°C)")
        ax.set_title("Grafik Suhu Surabaya")
        ax.grid(True)
        ax.legend()
        plt.tight_layout()

        self._clear_canvas()
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    
    # grafik curah hujan (tertanam)
    def chart_rain(self):
        months = list(data.index)
        rain = data["Curah_Hujan"].values

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(months, rain)
        ax.set_xticklabels(months, rotation=45)
        ax.set_ylabel("Curah Hujan (mm)")
        ax.set_title("Grafik Curah Hujan Surabaya")
        ax.grid(axis='y')
        plt.tight_layout()

        self._clear_canvas()
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


    # export laporan PDF
    def export_pdf(self):
        m = self.month_var.get()
        if m not in data.index:
            self._set_analysis_text("Tidak bisa export: data untuk bulan terpilih tidak tersedia.")
            return

        row = data.loc[m]
        avg, mx, mn, r = row["Suhu_Rata"], row["Suhu_Max"], row["Suhu_Min"], row["Curah_Hujan"]

        safe_month = m.replace(" ", "_")
        filename = f"Laporan_Iklim_Surabaya_{safe_month}.pdf"

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []

        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER
        )

        story.append(Paragraph("LAPORAN IKLIM SURABAYA", title_style))
        story.append(Spacer(1, 20))

        table_data = [
            ['Parameter', 'Nilai'],
            ['Suhu Rata-rata', f'{avg}°C'],
            ['Suhu Maksimum', f'{mx}°C'],
            ['Suhu Minimum', f'{mn}°C'],
            ['Curah Hujan', f'{r} mm']
        ]

        table = Table(table_data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"Dibuat pada: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))

        try:
            doc.build(story)
            self._set_analysis_text(f"PDF berhasil dibuat: {filename}")
        except Exception as e:
            self._set_analysis_text(f"Gagal membuat PDF: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ClimateApp()
    app.run()