# py -3.12 -m venv .venv
# source .venv/Scripts/activate
# pip install opencv-python face-recognition pillow
# pip install git+https://github.com/ageitgey/face_recognition_models

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
import face_recognition
from datetime import datetime
import os

class KYCSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KYC Registration System")
        self.root.geometry("800x600")
        
        self.user_data = {}
        self.id_card_front = None
        self.id_card_back = None
        self.id_face_encoding = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Registration Tab
        self.registration_frame = ttk.Frame(notebook)
        notebook.add(self.registration_frame, text="Registration")
        self.setup_registration_tab()
        
        # KYC Tab
        self.kyc_frame = ttk.Frame(notebook)
        notebook.add(self.kyc_frame, text="Face Verification")
        self.setup_kyc_tab()
        
    def setup_registration_tab(self):
        # Title
        title_label = ttk.Label(self.registration_frame, text="User Registration", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # User Information Frame
        info_frame = ttk.LabelFrame(self.registration_frame, text="Personal Information", 
                                   padding=20)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Name
        ttk.Label(info_frame, text="Full Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_entry = ttk.Entry(info_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Email
        ttk.Label(info_frame, text="Email:").grid(row=1, column=0, sticky='w', pady=5)
        self.email_entry = ttk.Entry(info_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Password
        ttk.Label(info_frame, text="Password:").grid(row=2, column=0, sticky='w', pady=5)
        self.password_entry = ttk.Entry(info_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # ID Card Upload Frame
        id_frame = ttk.LabelFrame(self.registration_frame, text="ID Card Upload", 
                                 padding=20)
        id_frame.pack(fill='x', padx=20, pady=10)
        
        # Front ID
        front_frame = ttk.Frame(id_frame)
        front_frame.pack(fill='x', pady=5)
        
        ttk.Label(front_frame, text="ID Card Front:").pack(side='left')
        self.front_button = ttk.Button(front_frame, text="Upload Front", 
                                      command=self.upload_front_id)
        self.front_button.pack(side='left', padx=10)
        self.front_status = ttk.Label(front_frame, text="Not uploaded", foreground='red')
        self.front_status.pack(side='left', padx=10)
        
        # Back ID
        back_frame = ttk.Frame(id_frame)
        back_frame.pack(fill='x', pady=5)
        
        ttk.Label(back_frame, text="ID Card Back:").pack(side='left')
        self.back_button = ttk.Button(back_frame, text="Upload Back", 
                                     command=self.upload_back_id)
        self.back_button.pack(side='left', padx=10)
        self.back_status = ttk.Label(back_frame, text="Not uploaded", foreground='red')
        self.back_status.pack(side='left', padx=10)
        
        # Register Button
        self.register_button = ttk.Button(self.registration_frame, text="Complete Registration", 
                                         command=self.register_user)
        self.register_button.pack(pady=20)
        
        # Status Label
        self.reg_status_label = ttk.Label(self.registration_frame, text="", 
                                         font=('Arial', 10))
        self.reg_status_label.pack(pady=5)
        
    def setup_kyc_tab(self):
        # Title
        title_label = ttk.Label(self.kyc_frame, text="Face Verification KYC", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = """
        Instructions for Face Verification:
        1. Make sure you are in good lighting
        2. Look directly at the camera
        3. Follow the on-screen prompts to move your head
        4. Keep your face centered in the frame
        """
        
        instruction_label = ttk.Label(self.kyc_frame, text=instructions, 
                                     justify='left', font=('Arial', 10))
        instruction_label.pack(pady=10)
        
        # Camera Frame
        self.camera_frame = ttk.Frame(self.kyc_frame)
        self.camera_frame.pack(pady=10)
        
        # Video Label
        self.video_label = ttk.Label(self.camera_frame)
        self.video_label.pack()
        
        # Status Frame
        status_frame = ttk.Frame(self.kyc_frame)
        status_frame.pack(pady=10)
        
        self.kyc_status_label = ttk.Label(status_frame, text="Ready to start verification", 
                                         font=('Arial', 12), foreground='blue')
        self.kyc_status_label.pack()
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                           maximum=100, length=300)
        self.progress_bar.pack(pady=5)
        
        # Control Buttons
        button_frame = ttk.Frame(self.kyc_frame)
        button_frame.pack(pady=10)
        
        self.start_kyc_button = ttk.Button(button_frame, text="Start Face Verification", 
                                          command=self.start_kyc)
        self.start_kyc_button.pack(side='left', padx=5)
        
        self.stop_kyc_button = ttk.Button(button_frame, text="Stop", 
                                         command=self.stop_kyc, state='disabled')
        self.stop_kyc_button.pack(side='left', padx=5)
        
        # KYC Variables
        self.cap = None
        self.kyc_running = False
        self.verification_steps = []
        self.current_step = 0
        self.step_frames = 0
        self.required_frames = 30  # Frames needed for each step
        
    def upload_front_id(self):
        file_path = filedialog.askopenfilename(
            title="Select ID Card Front",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                self.id_card_front = cv2.imread(file_path)
                self.front_status.config(text="Uploaded", foreground='green')
                
                # Extract face from ID card for comparison
                self.extract_id_face()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load front ID: {str(e)}")
                
    def upload_back_id(self):
        file_path = filedialog.askopenfilename(
            title="Select ID Card Back",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                self.id_card_back = cv2.imread(file_path)
                self.back_status.config(text="Uploaded", foreground='green')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load back ID: {str(e)}")
                
    def extract_id_face(self):
        """Extract face encoding from ID card for comparison"""
        if self.id_card_front is not None:
            try:
                # Convert BGR to RGB
                rgb_image = cv2.cvtColor(self.id_card_front, cv2.COLOR_BGR2RGB)
                
                # Find face encodings
                face_locations = face_recognition.face_locations(rgb_image)
                
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                    if face_encodings:
                        self.id_face_encoding = face_encodings[0]
                        print("Face extracted from ID card successfully")
                    else:
                        print("No face encoding found in ID card")
                else:
                    print("No face detected in ID card")
                    
            except Exception as e:
                print(f"Error extracting face from ID: {str(e)}")
                
    def register_user(self):
        """Register user with provided information"""
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not all([name, email, password]):
            self.reg_status_label.config(text="Please fill all fields", foreground='red')
            return
            
        if self.id_card_front is None or self.id_card_back is None:
            self.reg_status_label.config(text="Please upload both ID card images", 
                                        foreground='red')
            return
            
        # Store user data
        self.user_data = {
            'name': name,
            'email': email,
            'password': password,
            'registration_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.reg_status_label.config(text="Registration completed! Please proceed to Face Verification", 
                                    foreground='green')
        
        # Enable KYC tab
        messagebox.showinfo("Registration Complete", 
                          "Registration successful! Please go to Face Verification tab to complete KYC.")
        
    def start_kyc(self):
        """Start the KYC face verification process"""
        if not self.user_data:
            messagebox.showerror("Error", "Please complete registration first!")
            return
            
        if self.id_face_encoding is None:
            messagebox.showerror("Error", "No face found in ID card. Please upload a clear ID card image.")
            return
            
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Cannot access camera!")
                return
                
            self.kyc_running = True
            self.start_kyc_button.config(state='disabled')
            self.stop_kyc_button.config(state='normal')
            
            # Initialize verification steps
            self.verification_steps = [
                "Look straight at the camera",
                "Turn your head left slowly",
                "Turn your head right slowly",
                "Tilt your head up slightly",
                "Tilt your head down slightly",
                "Look straight again"
            ]
            
            self.current_step = 0
            self.step_frames = 0
            self.progress_var.set(0)
            
            # Start video thread
            self.video_thread = threading.Thread(target=self.kyc_video_loop)
            self.video_thread.daemon = True
            self.video_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
            
    def stop_kyc(self):
        """Stop the KYC verification process"""
        self.kyc_running = False
        if self.cap:
            self.cap.release()
        
        self.start_kyc_button.config(state='normal')
        self.stop_kyc_button.config(state='disabled')
        self.kyc_status_label.config(text="Verification stopped", foreground='red')
        self.progress_var.set(0)
        
    def kyc_video_loop(self):
        """Main video processing loop for KYC"""
        face_detected_frames = 0
        face_match_frames = 0
        
        while self.kyc_running:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in current frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Draw face rectangles and check for matches
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Compare with ID face
                if self.id_face_encoding is not None:
                    matches = face_recognition.compare_faces([self.id_face_encoding], 
                                                           face_encoding, tolerance=0.6)
                    
                    if matches[0]:
                        cv2.putText(frame, "MATCH", (left, top - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                        face_match_frames += 1
                    else:
                        cv2.putText(frame, "NO MATCH", (left, top - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                        
            # Update step progress
            if face_locations:
                face_detected_frames += 1
                self.step_frames += 1
                
                # Update progress
                step_progress = (self.step_frames / self.required_frames) * 100
                total_progress = (self.current_step / len(self.verification_steps)) * 100
                total_progress += step_progress / len(self.verification_steps)
                
                self.progress_var.set(min(total_progress, 100))
                
                # Check if current step is complete
                if self.step_frames >= self.required_frames:
                    self.current_step += 1
                    self.step_frames = 0
                    
                    if self.current_step >= len(self.verification_steps):
                        # KYC Complete
                        self.complete_kyc(face_match_frames, face_detected_frames)
                        break
                        
            # Update status label with current instruction
            if self.current_step < len(self.verification_steps):
                instruction = self.verification_steps[self.current_step]
                progress_text = f"Step {self.current_step + 1}/{len(self.verification_steps)}: {instruction}"
                self.kyc_status_label.config(text=progress_text, foreground='blue')
            
            # Add instruction text to frame
            if self.current_step < len(self.verification_steps):
                cv2.putText(frame, self.verification_steps[self.current_step], 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
            # Convert frame to display in tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_pil = frame_pil.resize((640, 480))
            frame_tk = ImageTk.PhotoImage(frame_pil)
            
            # Update video label
            self.video_label.config(image=frame_tk)
            self.video_label.image = frame_tk
            
            time.sleep(0.03)  # ~30 FPS
            
        if self.cap:
            self.cap.release()
            
    def complete_kyc(self, match_frames, total_frames):
        """Complete KYC process and show results"""
        self.kyc_running = False
        
        # Calculate match percentage
        match_percentage = (match_frames / total_frames) * 100 if total_frames > 0 else 0
        
        # Determine if KYC passed
        kyc_passed = match_percentage > 70  # Require 70% match rate
        
        if kyc_passed:
            self.kyc_status_label.config(text=f"KYC PASSED! Match rate: {match_percentage:.1f}%", 
                                        foreground='green')
            messagebox.showinfo("KYC Complete", 
                              f"Face verification successful!\n"
                              f"Match rate: {match_percentage:.1f}%\n"
                              f"User: {self.user_data['name']}\n"
                              f"Status: VERIFIED")
        else:
            self.kyc_status_label.config(text=f"KYC FAILED! Match rate: {match_percentage:.1f}%", 
                                        foreground='red')
            messagebox.showerror("KYC Failed", 
                               f"Face verification failed!\n"
                               f"Match rate: {match_percentage:.1f}%\n"
                               f"Please try again with better lighting or ensure you're using your own ID.")
        
        self.progress_var.set(100)
        self.start_kyc_button.config(state='normal')
        self.stop_kyc_button.config(state='disabled')
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    # Note: You need to install required packages:
    # pip install opencv-python face-recognition pillow
    
    try:
        app = KYCSystem()
        app.run()
    except ImportError as e:
        print("Missing required packages. Please install:")
        print("pip install opencv-python face-recognition pillow")
        print(f"Error: {e}")
    except Exception as e:
        print(f"Application error: {e}")