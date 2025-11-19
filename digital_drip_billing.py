# digital_drip_billing.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import datetime
import os

# Optional libraries
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    reportlab_available = True
except Exception:
    reportlab_available = False

try:
    import qrcode
    from PIL import Image, ImageTk
    qr_available = True
except Exception:
    qr_available = False
    try:
        # allow Logo rendering on UI if Pillow is present
        from PIL import Image, ImageTk
    except Exception:
        Image = ImageTk = None

# ---------------- Config (edit these) ----------------
CAFE_DETAILS = {
    "name": "Digital Drip Café",
    "address_lines": [
        "Ground Floor, Tech Innovation Hub",
        "Near Central Library",
        "Sundernagar, Himachal Pradesh – 175002"
    ],
    "upi_vpa": "digitaldripcafe@upi",   # <- replace with your real VPA to enable real payments
    "upi_name": "Digital Drip Café",
    "upi_note": "Digital Drip Café Bill"
}

PRICES = {
    "Latte": 120,
    "Espresso": 100,
    "Cappuccino": 150,
    "Cold Coffee": 130,
    "Sandwich": 90,
    "Burger": 120,
    "Momos": 80,
    "French Fries": 70
}

THEMES = {
    "light": {
        "bg": "#F4F7FA",
        "card": "#FFFFFF",
        "text": "#1F2937",
        "muted": "#6B7280",
        "accent": "#1E40AF",
        "btn_fg": "#FFFFFF",
        "entry_bg": "#F9FAFB",
        "bill_bg": "#FFFFFF",
        "button_color": "#1E40AF",
    },
    "dark": {
        "bg": "#0F1724",
        "card": "#0B1220",
        "text": "#E6EEF6",
        "muted": "#9CA3AF",
        "accent": "#F59E0B",
        "btn_fg": "#0B1220",
        "entry_bg": "#0B1220",
        "bill_bg": "#071126",
        "button_color": "#F59E0B",
    },
}

# ---------------- App ----------------
class CafeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{CAFE_DETAILS['name']} — Billing System")
        self.geometry("1000x680")
        self.minsize(900, 620)

        # theme
        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]

        # data
        self.qty_vars = {k: tk.IntVar(value=0) for k in PRICES}
        self.customer_name_var = tk.StringVar(value="")
        self.customer_phone_var = tk.StringVar(value="")

        # logo (optional: place logo.png in same folder)
        self.logo_path = "logo.png"
        self.logo_image = None
        if os.path.exists(self.logo_path) and 'Image' in globals() and Image is not None:
            try:
                img = Image.open(self.logo_path)
                img.thumbnail((120, 120), Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
            except Exception:
                self.logo_image = None

        self._last_bill = None
        self._build_ui()
        self.apply_theme(self.theme_name)

    def _build_ui(self):
        # layout columns
        self.columnconfigure(0, weight=1, uniform="a")
        self.columnconfigure(1, weight=1, uniform="a")
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        # Topbar
        topbar = tk.Frame(self, bg=self.theme["card"], bd=0)
        topbar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        topbar.columnconfigure(0, weight=1)
        topbar.columnconfigure(1, weight=1)

        title = tk.Label(topbar, text="☕ " + CAFE_DETAILS["name"], font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=20, pady=12)

        toggle_frame = tk.Frame(topbar)
        toggle_frame.grid(row=0, column=1, sticky="e", padx=20)
        self.theme_btn = ttk.Checkbutton(toggle_frame, text="Light Mode", command=self.toggle_theme)
        self.theme_btn.pack(anchor="e")

        # Left: Menu & Customer details
        left_card = tk.Frame(self, bd=0, padx=12, pady=12)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(20,10), pady=20)
        left_card.columnconfigure(0, weight=1)

        left_title = tk.Label(left_card, text="Menu", font=("Segoe UI", 18, "bold"))
        left_title.grid(row=0, column=0, sticky="w", pady=(4,12))

        # Customer fields
        cust_frame = tk.Frame(left_card)
        cust_frame.grid(row=1, column=0, sticky="ew", pady=(0,10))
        cust_frame.columnconfigure(1, weight=1)

        tk.Label(cust_frame, text="Customer Name:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0,6))
        tk.Entry(cust_frame, textvariable=self.customer_name_var, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="ew")

        tk.Label(cust_frame, text="Phone:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0,6), pady=(6,0))
        tk.Entry(cust_frame, textvariable=self.customer_phone_var, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="ew", pady=(6,0))

        # Menu list
        menu_frame = tk.Frame(left_card)
        menu_frame.grid(row=2, column=0, sticky="nsew", pady=(12,0))
        for i in range(2):
            menu_frame.columnconfigure(i, weight=1)

        r = 0
        for item, price in PRICES.items():
            lbl = tk.Label(menu_frame, text=f"{item} — ₹{price}", anchor="w", font=("Segoe UI", 12))
            lbl.grid(row=r, column=0, sticky="w", padx=(6,10), pady=6)
            spin = tk.Spinbox(menu_frame, from_=0, to=99, width=6, textvariable=self.qty_vars[item],
                              font=("Segoe UI", 12), justify="center")
            spin.grid(row=r, column=1, sticky="e", padx=(10,6))
            r += 1

        note = tk.Label(left_card, text="Set quantities and customer details, then click Generate Bill.", font=("Segoe UI", 10, "italic"))
        note.grid(row=3, column=0, sticky="w", pady=(12,0))

        # Right: Bill area
        right_card = tk.Frame(self, bd=0, padx=6, pady=6)
        right_card.grid(row=1, column=1, sticky="nsew", padx=(10,20), pady=20)
        right_card.rowconfigure(1, weight=1)
        right_card.columnconfigure(0, weight=1)

        bill_title = tk.Label(right_card, text="Bill Receipt", font=("Segoe UI", 18, "bold"))
        bill_title.grid(row=0, column=0, sticky="w", pady=(4,8))

        bill_frame = tk.Frame(right_card, bd=1, relief="sunken")
        bill_frame.grid(row=1, column=0, sticky="nsew")

        # show UI logo if available
        if self.logo_image is not None:
            logo_lbl = tk.Label(bill_frame, image=self.logo_image, bd=0)
            logo_lbl.pack(anchor="n", pady=(8,4))

        self.bill_text = tk.Text(bill_frame, wrap="none", font=("Consolas", 11), bd=0)
        vsb = tk.Scrollbar(bill_frame, orient="vertical", command=self.bill_text.yview)
        self.bill_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.bill_text.pack(side="left", fill="both", expand=True)

        # Buttons
        buttons = tk.Frame(right_card)
        buttons.grid(row=2, column=0, sticky="ew", pady=12)
        for i in range(5):
            buttons.columnconfigure(i, weight=1)

        gen_btn = tk.Button(buttons, text="Generate Bill", command=self.generate_bill, font=("Segoe UI", 11, "bold"))
        gen_btn.grid(row=0, column=0, padx=6, sticky="ew")

        save_txt_btn = tk.Button(buttons, text="Save Bill (TXT)", command=self.save_bill, font=("Segoe UI", 11))
        save_txt_btn.grid(row=0, column=1, padx=6, sticky="ew")

        save_pdf_btn = tk.Button(buttons, text="Save as PDF", command=self.save_pdf, font=("Segoe UI", 11))
        save_pdf_btn.grid(row=0, column=2, padx=6, sticky="ew")

        qr_btn = tk.Button(buttons, text="Generate UPI QR", command=self.generate_upi_qr, font=("Segoe UI", 11))
        qr_btn.grid(row=0, column=3, padx=6, sticky="ew")

        clear_btn = tk.Button(buttons, text="Reset", command=self.reset_all, font=("Segoe UI", 11))
        clear_btn.grid(row=0, column=4, padx=6, sticky="ew")

        # Status
        self.status = tk.Label(self, text="", anchor="w", font=("Segoe UI", 10))
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0,12))

        # store theme widgets
        self._widgets_for_theme = {
            "topbar": topbar,
            "title": title,
            "note": note,
            "bill_frame": bill_frame,
            "bill_text": self.bill_text,
            "gen_btn": gen_btn,
            "save_txt_btn": save_txt_btn,
            "save_pdf_btn": save_pdf_btn,
            "qr_btn": qr_btn,
            "clear_btn": clear_btn,
            "status": self.status,
            "labels": [w for w in menu_frame.grid_slaves() if isinstance(w, tk.Label)],
            "spinboxes": [w for w in menu_frame.grid_slaves() if isinstance(w, tk.Spinbox)],
        }

    def apply_theme(self, name):
        t = THEMES[name]
        self.configure(bg=t["bg"])
        self._widgets_for_theme["topbar"].configure(bg=t["card"])
        self._widgets_for_theme["title"].configure(bg=t["card"], fg=t["accent"])
        self._widgets_for_theme["note"].configure(bg=t["card"], fg=t["muted"])
        for lbl in self._widgets_for_theme["labels"]:
            lbl.configure(bg=t["card"], fg=t["text"])
        for spin in self._widgets_for_theme["spinboxes"]:
            spin.configure(bg=t["entry_bg"], fg=t["text"], insertbackground=t["text"], relief="solid")
        self._widgets_for_theme["bill_frame"].configure(bg=t["bill_bg"])
        self._widgets_for_theme["bill_text"].configure(bg=t["bill_bg"], fg=t["text"], insertbackground=t["text"])
        btn_bg = t["button_color"]
        self._widgets_for_theme["gen_btn"].configure(bg=btn_bg, fg=t["btn_fg"])
        self._widgets_for_theme["save_txt_btn"].configure(bg=btn_bg, fg=t["btn_fg"])
        self._widgets_for_theme["save_pdf_btn"].configure(bg=btn_bg, fg=t["btn_fg"])
        self._widgets_for_theme["qr_btn"].configure(bg=btn_bg, fg=t["btn_fg"])
        self._widgets_for_theme["clear_btn"].configure(bg="#9CA3AF" if name == "light" else "#334155", fg=t["btn_fg"])
        self._widgets_for_theme["status"].configure(bg=t["bg"], fg=t["muted"])
        if name == "light":
            self.theme_btn.config(text="Light Mode")
        else:
            self.theme_btn.config(text="Dark Mode")

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self.apply_theme(self.theme_name)

    # Build bill header text
    def _bill_header_text(self, bill_no, now):
        lines = []
        lines.append(f"    {CAFE_DETAILS['name']}")
        for ln in CAFE_DETAILS["address_lines"]:
            lines.append(f"    {ln}")
        # customer info
        cname = self.customer_name_var.get().strip()
        cphone = self.customer_phone_var.get().strip()
        if cname or cphone:
            lines.append(f"    Customer: {cname}   Phone: {cphone}")
        lines.append(f"    Bill No: {bill_no}    Date: {now}")
        lines.append("-" * 56)
        lines.append("{:<28}{:<6}{:>12}".format("ITEM", "QTY", "TOTAL"))
        lines.append("-" * 56)
        return "\n".join(lines) + "\n"

    def generate_bill(self):
        self.bill_text.delete("1.0", "end")
        bill_no = random.randint(10000, 99999)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = self._bill_header_text(bill_no, now)
        self.bill_text.insert("end", header)

        subtotal = 0
        for item, var in self.qty_vars.items():
            qty = var.get()
            if qty > 0:
                total_price = PRICES[item] * qty
                subtotal += total_price
                self.bill_text.insert("end", "{:<28}{:<6}{:>12}\n".format(item, qty, f"₹{total_price}"))

        self.bill_text.insert("end", "-" * 56 + "\n")
        gst = round(subtotal * 0.05, 2)
        grand = round(subtotal + gst, 2)
        self.bill_text.insert("end", "{:<28}{:<6}{:>12}\n".format("Subtotal", "", f"₹{subtotal}"))
        self.bill_text.insert("end", "{:<28}{:<6}{:>12}\n".format("GST (5%)", "", f"₹{gst}"))
        self.bill_text.insert("end", "{:<28}{:<6}{:>12}\n".format("Total", "", f"₹{grand}"))

        self.status.config(text=f"Bill generated — Total ₹{grand}")
        self._last_bill = {"bill_no": bill_no, "datetime": now, "subtotal": subtotal, "gst": gst, "grand": grand}

    def save_bill(self):
        content = self.bill_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("No Bill", "Generate the bill first before saving.")
            return
        if not os.path.exists("bills"):
            os.makedirs("bills")
        fname = f"bills/bill_{random.randint(1000,9999)}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Saved", f"Bill saved as {fname}")
        self.status.config(text=f"Saved: {fname}")

    def save_pdf(self):
        if not self._last_bill:
            messagebox.showwarning("No Bill", "Generate the bill first.")
            return
        if not reportlab_available:
            messagebox.showerror("Missing package", "reportlab is required to save PDF.\nRun:\n\npip install reportlab")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
                                             initialfile=f"bill_{self._last_bill['bill_no']}.pdf")
        if not fpath:
            return

        try:
            c = canvas.Canvas(fpath, pagesize=A4)
            width, height = A4
            y = height - 50

            # logo if present
            if os.path.exists(self.logo_path):
                try:
                    c.drawImage(self.logo_path, 40, y-80, width=100, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass

            c.setFont("Helvetica-Bold", 14)
            c.drawString(160, y-20, CAFE_DETAILS["name"])
            c.setFont("Helvetica", 10)
            for i, ln in enumerate(CAFE_DETAILS["address_lines"]):
                c.drawString(160, y-40 - (i * 12), ln)

            # customer
            cname = self.customer_name_var.get().strip()
            cphone = self.customer_phone_var.get().strip()
            y -= 90
            c.setFont("Courier", 10)
            c.drawString(40, y, f"Bill No: {self._last_bill['bill_no']}    Date: {self._last_bill['datetime']}")
            y -= 16
            if cname or cphone:
                c.drawString(40, y, f"Customer: {cname}    Phone: {cphone}")
                y -= 16

            c.drawString(40, y, "-" * 90)
            y -= 16
            c.drawString(40, y, "{:<40}{:<8}{:>12}".format("ITEM", "QTY", "TOTAL"))
            y -= 14
            c.drawString(40, y, "-" * 90)
            y -= 18

            for item, var in self.qty_vars.items():
                qty = var.get()
                if qty > 0:
                    total = PRICES[item] * qty
                    line = "{:<40}{:<8}{:>12}".format(item, qty, f"₹{total}")
                    c.drawString(40, y, line)
                    y -= 16
                    if y < 80:
                        c.showPage()
                        y = height - 50

            y -= 8
            c.drawString(40, y, "-" * 90)
            y -= 16
            c.drawRightString(560, y, f"Subtotal: ₹{self._last_bill['subtotal']:.2f}")
            y -= 14
            c.drawRightString(560, y, f"GST (5%): ₹{self._last_bill['gst']:.2f}")
            y -= 14
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(560, y, f"Total: ₹{self._last_bill['grand']:.2f}")

            # embed UPI QR if qrcode installed
            if qr_available:
                try:
                    vpa = CAFE_DETAILS.get("upi_vpa", "")
                    pname = CAFE_DETAILS.get("upi_name", "")
                    note = CAFE_DETAILS.get("upi_note", "")
                    amount = self._last_bill["grand"]
                    upi_uri = f"upi://pay?pa={vpa}&pn={pname}&am={amount}&cu=INR&tn={note}"
                    qr = qrcode.make(upi_uri)
                    tmp_qr = "tmp_upi_qr.png"
                    qr.save(tmp_qr)
                    c.drawImage(tmp_qr, 40, 40, width=120, height=120, preserveAspectRatio=True, mask='auto')
                    try:
                        os.remove(tmp_qr)
                    except Exception:
                        pass
                except Exception:
                    pass

            c.save()
            messagebox.showinfo("PDF Saved", f"Saved PDF to {fpath}")
            self.status.config(text=f"PDF saved: {fpath}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to create PDF:\n{e}")

    def generate_upi_qr(self):
        if not self._last_bill:
            messagebox.showwarning("No Bill", "Generate the bill first.")
            return
        if not qr_available:
            messagebox.showerror("Missing packages", "qrcode and pillow are required to generate UPI QR.\nRun:\n\npip install qrcode[pil] pillow")
            return

        amount = self._last_bill["grand"]
        vpa = CAFE_DETAILS.get("upi_vpa", "")
        pname = CAFE_DETAILS.get("upi_name", "")
        note = CAFE_DETAILS.get("upi_note", "")

        if not vpa or "enter-your-vpa" in vpa or "your-vpa" in vpa:
            messagebox.showwarning("UPI ID Required", "Please set a valid UPI VPA in the configuration before generating QR.")
            return

        upi_uri = f"upi://pay?pa={vpa}&pn={pname}&am={amount}&cu=INR&tn={note}"

        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(upi_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # show in popup
        top = tk.Toplevel(self)
        top.title("UPI QR — Scan to Pay")
        img.thumbnail((300, 300), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(top, image=photo)
        lbl.image = photo
        lbl.pack(padx=12, pady=12)
        tk.Label(top, text=f"Amount: ₹{amount}", font=("Segoe UI", 12, "bold")).pack()
        tk.Label(top, text=f"UPI: {vpa}", font=("Segoe UI", 10)).pack()

        def save_qr_file():
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG image", "*.png")],
                                                initialfile=f"upi_bill_{self._last_bill['bill_no']}.png")
            if not path:
                return
            try:
                img.save(path)
                messagebox.showinfo("Saved", f"QR saved to {path}")
            except Exception as e:
                messagebox.showerror("Save error", str(e))

        tk.Button(top, text="Save QR", command=save_qr_file).pack(pady=(8,12))

    def reset_all(self):
        for var in self.qty_vars.values():
            var.set(0)
        self.customer_name_var.set("")
        self.customer_phone_var.set("")
        self.bill_text.delete("1.0", "end")
        self.status.config(text="Reset done")
        self._last_bill = None

if __name__ == "__main__":
    app = CafeApp()
    app.mainloop()
