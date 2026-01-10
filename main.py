import tkinter as tk
from View.main_view import TkinterPDFView # Adjusted import path
from Controller.main_controller import PDFController
# from view_tkinter import TkinterPDFView
# from controller import PDFController

def main():
    root = tk.Tk()
    root.title("Modular PDF Viewer Pro - Text Layer Ready")
    root.geometry("1100x850")
    
    # Dependency Injection
    app = TkinterPDFView(root, PDFController)
    
    root.mainloop()

if __name__ == "__main__":
    main()