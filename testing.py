import customtkinter as ctk

def button_callback():
    print("Button clicked!")
    label.configure(text=entry.get())

# Set appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Create window
app = ctk.CTk()
app.geometry("400x300")

# Create widgets
frame = ctk.CTkFrame(master=app)
frame.pack(pady=20, padx=60, fill="both", expand=True)

label = ctk.CTkLabel(master=frame, text="CustomTkinter Example")
label.pack(pady=12, padx=10)

entry = ctk.CTkEntry(master=frame, placeholder_text="Enter text")
entry.pack(pady=12, padx=10)

button = ctk.CTkButton(master=frame, text="Click Me", command=button_callback)
button.pack(pady=12, padx=10)

checkbox = ctk.CTkCheckBox(master=frame, text="Remember me")
checkbox.pack(pady=12, padx=10)

# Run application
app.mainloop()