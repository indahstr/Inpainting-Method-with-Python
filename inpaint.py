import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os

class ImageHistory:
    def __init__(self):
        self.history = []
        self.current_index = -1

    def add(self, img, mask):
        self.history = self.history[:self.current_index + 1]
        self.history.append((img.copy(), mask.copy()))
        self.current_index += 1

    def undo(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]
        return None, None

    def redo(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        return None, None

def process_image(img, mask, inpainting_method):
    # Konversi gambar ke grayscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Terapkan filter median untuk menghilangkan noise
    img_gray = cv2.medianBlur(img_gray, 5)

    # Buat mask gambar yang kosong jika belum ada
    if mask is None:
        mask = np.zeros(img_gray.shape, np.uint8)

    # Terapkan inpainting pada gambar dengan mask berdasarkan metode yang dipilih
    if inpainting_method == 'TELEA':
        img_result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    elif inpainting_method == 'NS':
        img_result = cv2.inpaint(img, mask, 3, cv2.INPAINT_NS)

    return img_result, mask

def mouse_event(event, x, y, flags, param):
    global img, mask

    if event == cv2.EVENT_LBUTTONDOWN:
        box_size = param["box_size"]
        # Buat kotak seleksi dengan ukuran piksel yang ditentukan di sekitar titik yang diklik
        roi = img[max(y-box_size//2, 0):y+box_size//2, max(x-box_size//2, 0):x+box_size//2]

        # Terapkan proses thresholding pada gambar ROI
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, roi_mask = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

        # Terapkan erosi dan dilasi pada mask untuk menghilangkan noise kecil
        roi_mask = cv2.erode(roi_mask, np.ones((3, 3), np.uint8), iterations=1)
        roi_mask = cv2.dilate(roi_mask, np.ones((3, 3), np.uint8), iterations=1)

        # Tempatkan mask pada gambar
        mask[max(y-box_size//2, 0):y+box_size//2, max(x-box_size//2, 0):x+box_size//2] = roi_mask

        # Terapkan proses inpainting pada gambar
        img, mask = process_image(img, mask, inpainting_method)

        # Tampilkan gambar dengan mask
        cv2.imshow("image", img)
        if mask is not None:
            cv2.imshow("mask", mask)

        # Tambahkan perubahan ke riwayat
        history.add(img, mask)

    elif event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
        box_size = param["box_size"]
        # Buat garis dengan ketebalan 10 piksel pada mask untuk mengikuti gerakan cursor
        cv2.line(mask, (x, y), (x, y), 255, 10)

        # Terapkan proses inpainting pada gambar
        img, mask = process_image(img, mask, inpainting_method)

        # Tampilkan gambar dengan mask
        cv2.imshow("image", img)
        if mask is not None:
            cv2.imshow("mask", mask)

def choose_image():
    global file_path, img, mask
    file_path = filedialog.askopenfilename()

    if file_path:
        # Mengimpor gambar
        img = cv2.imread(file_path)

        # Membatasi lebar gambar menjadi 600 piksel
        img = cv2.resize(img, (600, int(600 * img.shape[0] / img.shape[1])))

        # Menginisialisasi mask dengan array kosong
        mask = np.zeros(img.shape[:2], dtype=np.uint8)

        # Inisialisasi metode inpainting yang digunakan
        inpainting_method = 'TELEA'

        # Tampilkan gambar dengan mask awal
        cv2.imshow("image", img)
        cv2.imshow("mask", mask)

        # Reset riwayat
        history.history = []
        history.current_index = -1

        # Tambahkan perubahan awal ke riwayat
        history.add(img, mask)

def process_image_with_method(method):
    global img, mask
    inpainting_method = method.upper()
    img, mask = process_image(img, mask, inpainting_method)

    # Tampilkan gambar dengan mask
    cv2.imshow("image", img)
    if mask is not None:
        cv2.imshow("mask", mask)

    # Tambahkan perubahan ke riwayat
    history.add(img, mask)

def reset_image():
    global img, mask
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    img = cv2.imread(file_path)
    img = cv2.resize(img, (600, int(600 * img.shape[0] / img.shape[1])))
    img, mask = process_image(img, mask, inpainting_method)

    # Tampilkan gambar dengan mask
    cv2.imshow("image", img)
    if mask is not None:
        cv2.imshow("mask", mask)

    # Tambahkan perubahan ke riwayat
    history.add(img, mask)

def save_image():
    global img
    if img is not None:
        save_path = filedialog.asksaveasfilename(defaultextension=".png")
        if save_path:
            cv2.imwrite(save_path, img)
            messagebox.showinfo("Save Image", "Image saved successfully!")
        else:
            messagebox.showinfo("Save Image", "Save operation cancelled.")
    else:
        messagebox.showinfo("Save Image", "No image to save.")

def save_mask():
    global mask
    if mask is not None:
        save_path = filedialog.asksaveasfilename(defaultextension=".png")
        if save_path:
            cv2.imwrite(save_path, mask)
            messagebox.showinfo("Save Mask", "Mask saved successfully!")
        else:
            messagebox.showinfo("Save Mask", "Save operation cancelled.")
    else:
        messagebox.showinfo("Save Mask", "No mask to save.")

def change_box_size():
    global param
    box_size = simpledialog.askinteger("Change Box Size", "Enter the box size:")
    if box_size is not None:
        param["box_size"] = box_size

def undo():
    global img, mask
    img, mask = history.undo()

    # Tampilkan gambar dengan mask
    cv2.imshow("image", img)
    if mask is not None:
        cv2.imshow("mask", mask)

def redo():
    global img, mask
    img, mask = history.redo()

    # Tampilkan gambar dengan mask
    cv2.imshow("image", img)
    if mask is not None:
        cv2.imshow("mask", mask)

root = tk.Tk()
root.title("Inpainting Application")

# Membuat menu strip
menubar = tk.Menu(root)

# Membuat menu "File"
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Open Image", command=choose_image)
file_menu.add_command(label="Save Image", command=save_image)
file_menu.add_command(label="Save Mask", command=save_mask)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

# Membuat menu "Method"
method_menu = tk.Menu(menubar, tearoff=0)
method_menu.add_command(label="TELEA", command=lambda: process_image_with_method("TELEA"))
method_menu.add_command(label="NS", command=lambda: process_image_with_method("NS"))
menubar.add_cascade(label="Method", menu=method_menu)

# Membuat menu "Edit"
edit_menu = tk.Menu(menubar, tearoff=0)
edit_menu.add_command(label="Undo", command=undo)
edit_menu.add_command(label="Redo", command=redo)
edit_menu.add_command(label="Reset", command=reset_image)
edit_menu.add_separator()
edit_menu.add_command(label="Change Box Size", command=change_box_size)
menubar.add_cascade(label="Edit", menu=edit_menu)

# Menghubungkan menu strip dengan root window
root.config(menu=menubar)

# Variabel global
file_path = ""
img = None
mask = None
inpainting_method = "TELEA"
param = {"box_size": 20}

# Membuat window image
cv2.namedWindow("image")
cv2.namedWindow("mask")

# Mengatur posisi jendela mask
cv2.moveWindow("mask", 600, 0)

# Menambahkan event mouse pada gambar
cv2.setMouseCallback("image", mouse_event, param)

# Membuat objek ImageHistory
history = ImageHistory()

root.mainloop()
