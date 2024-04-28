# delphi.py
# An auxilary GUI for the Oracle Easy Open Source Modular Interpreter System
# An open source project by Mnemosyne Labs, a divison of Azoth Corp (2024)


# User can access in terminal with 'open aux gui' or by mentioning needing one


import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Text
from ttkbootstrap import Style, Floodgauge
from ttkbootstrap.widgets import Frame, Button, Label, Entry, Scrollbar, Notebook, Meter, Scale, Checkbutton
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import os
from datetime import datetime 
import json
from user import USER_THEMES
import threading
import subprocess
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import time
import openai
import anthropic
import pygame
import sys
from io import StringIO
import psutil
import signal
import queue


# Its serving graphics:
class OracleGUI:
    """
    The main class for the Oracle Interpreter graphical user interface (GUI).
    
    This class handles the creation and functionality of the GUI, including setting up the main window,
    creating various tabs and panels, and managing user interactions with the Oracle Interpreter.
    
    Attributes:
        oracle_interpreter (OracleInterpreter): An instance of the OracleInterpreter class.
        controller (OracleController): An instance of the OracleController class.
        root (tk.Tk): The main window of the GUI.
        canvas (tk.Canvas): The canvas widget for displaying the background image.
        bg_photo (ImageTk.PhotoImage): The background image for the GUI.
        conversation_text (tk.Text): The text widget for displaying the conversation.
        user_input (tk.Entry): The entry widget for user input.
        temperature_meter (ttkbootstrap.Meter): The meter widget for adjusting the temperature setting.
        max_tokens_meter (ttkbootstrap.Meter): The meter widget for adjusting the max_tokens setting.
        provider_var (tk.StringVar): The variable for storing the selected LLM provider.
        api_key_entry (tk.Entry): The entry widget for the API key.
        processing_label (ttkbootstrap.Label): The label for indicating processing status.
        floodgauge (ttkbootstrap.Floodgauge): The floodgauge widget for displaying processing progress.
        status_label (ttkbootstrap.Label): The label for displaying the status.
        terminal_output (str): The variable for storing the terminal output.
        terminal_thread (threading.Thread): The thread for capturing terminal output.
        floodgauge_animation_thread (threading.Thread): The thread for animating the floodgauge.
        floodgauge_animation_running (bool): The flag for indicating if the floodgauge animation is running.
    """
   
    def __init__(self, oracle_interpreter, controller, queue):
        """
        Initialize the OracleGUI.
        
        Args:
            oracle_interpreter (OracleInterpreter): An instance of the OracleInterpreter class.
            controller (OracleController): An instance of the OracleController class.
        """
        self.oracle_interpreter = oracle_interpreter
        self.controller = controller
        self.queue = queue
    
        
        
        
        # GUI Terminal Lock killswitch flag
        self.stop_event = threading.Event()
        
        # Initialize the session log file
        self.session_log_file = self.create_session_log_file()

        # Create a new style
        app = Style(theme='nightcity')
        self.root = app.master

        # Create the Boolean for enabling the OS+Browser functions
        self.llm_web_browser_enabled = tk.BooleanVar(value=False)
        
        self.root.wm_deiconify()
        self.root.title("Oracle Interpreter Control Panel")
        self.root.geometry("1150x900")

        self.aetherion_directory = "Aetherion"
        self.athenium_directory = "Athenium"
        self.acheron_directory = "Acheron"
        
        
        
        
        # Set the background image
        bg_image_path = "oracle_background.png"
        self.bg_image = Image.open(bg_image_path)


        # Set the window icon
        icon_path = "oracle_icon.ico"
        self.root.iconbitmap(default=icon_path)


        # Create a canvas for the background image
        self.canvas = tk.Canvas(self.root, width=1150, height=900)
        self.canvas.pack(fill='both', expand=True)

        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor='nw')


        # Bind the resize event to update the background image
        self.canvas.bind('<Configure>', self.resize_background_image)



        # Create a notebook widget for tabs
        notebook = Notebook(self.canvas)
        notebook.place(relx=0.5, rely=0.5, relwidth=0.75, relheight=0.75, anchor='center')



        # Create tabs
        main_tab = Frame(notebook)
        settings_tab = Frame(notebook)
        api_tab = Frame(notebook)

        notebook.add(main_tab, text="Main")
        notebook.add(settings_tab, text="Settings")
        notebook.add(api_tab, text="API Control")


        # Create the main frame
        main_frame = Frame(main_tab, padding=10, bootstyle="primary")
        main_frame.pack(fill='both', expand=True)
        
        
        # Create the left panel
        left_panel = Frame(main_frame)
        left_panel.pack(side='left', fill='y', padx=10, pady=10)





        # Create a Style object
        style = Style()

        # Create custom styles for each button
        style.configure("Start.TButton", background="#3af180", foreground="black")
        style.configure("Pause.TButton", background="#ffbd05", foreground="black")
        style.configure("Stop.TButton", background="#ff0000", foreground="white")  # Updated to red alert color
        style.configure("Antikythera.TButton", background="#b87333", foreground="white")  # Updated to copper/bronze color
        style.configure("Alexandria.TButton", background="#1e00e0", foreground="white")
        style.configure("Aetherion.TButton", background="royal blue", foreground="white")
        style.configure("Athenium.TButton", background="orange red", foreground="white")
        style.configure("Acheron.TButton", background="forest green", foreground="white")
        style.configure("OpenLogs.TButton", background="light yellow", foreground="black")
        style.configure("SaveConversation.TButton", background="#cd0532", foreground="white")  # Updated to previous Antikythera color
        style.configure("TerminateSystem.TButton", background="black", foreground="#ff0000")  # Added terminate system button style

        # Create buttons using the custom styles
        start_button = Button(left_panel, text="Start/Resume Oracle Interpreter", command=self.start_or_resume_oracle_interpreter, style="Start.TButton")
        start_button.pack(pady=10, fill='x')
        ToolTip(start_button, text="Start or resume the Oracle Interpreter (broken)", bootstyle=("success", "inverse"))

        pause_button = Button(left_panel, text="Pause Oracle Interpreter", command=self.pause_oracle_interpreter, style="Pause.TButton")
        pause_button.pack(pady=10, fill='x')
        ToolTip(pause_button, text="Pause the Oracle Interpreter (broken)", bootstyle=("warning", "inverse"))

        stop_button = Button(left_panel, text="Stop Oracle Interpreter", command=self.stop_oracle_interpreter, style="Stop.TButton")
        stop_button.pack(pady=10, fill='x')
        ToolTip(stop_button, text="Stop the Oracle Interpreter (broken)", bootstyle=("danger", "inverse"))

        antikythera_button = Button(left_panel, text="Open Antikythera Directory", command=self.open_antikythera_directory, style="Antikythera.TButton")
        antikythera_button.pack(pady=10, fill='x')
        ToolTip(antikythera_button, text="Workspace directory", bootstyle=(INFO, INVERSE))

        alexandria_button = Button(left_panel, text="Open Alexandria Directory", command=self.open_alexandria_directory, style="Alexandria.TButton")
        alexandria_button.pack(pady=10, fill='x')
        ToolTip(alexandria_button, text="Long-term memory directory", bootstyle=(DARK, INVERSE))

        aetherion_button = Button(left_panel, text="Open Aetherion Directory", command=self.open_aetherion_directory, style="Aetherion.TButton")
        aetherion_button.pack(pady=10, fill='x')
        ToolTip(aetherion_button, text="Analytic long-term storage directory", bootstyle=("royal-blue", "inverse"))

        athenium_button = Button(left_panel, text="Open Athenium Directory", command=self.open_athenium_directory, style="Athenium.TButton")
        athenium_button.pack(pady=10, fill='x')
        ToolTip(athenium_button, text="Short-term memory directory", bootstyle=("vermillion", "inverse"))

        acheron_button = Button(left_panel, text="Open Acheron Directory", command=self.open_acheron_directory, style="Acheron.TButton")
        acheron_button.pack(pady=10, fill='x')
        ToolTip(acheron_button, text="Creative and emotional content storage directory", bootstyle=("forest-green", "inverse"))

        open_logs_button = Button(left_panel, text="Open Logs", command=lambda: self.open_logs_folder(), style="OpenLogs.TButton")
        open_logs_button.pack(pady=10, fill='x')
        ToolTip(open_logs_button, text="Open the folder containing interaction logs", bootstyle=("pale-yellow", "inverse"))

        save_conversation_button = Button(left_panel, text="Save Conversation", command=lambda: self.save_conversation(), style="SaveConversation.TButton")
        save_conversation_button.pack(pady=10, fill='x')
        ToolTip(save_conversation_button, text="Save the current conversation to a JSONL file", bootstyle=("bubblegum-pink", "inverse"))

        terminate_system_button = Button(left_panel, text="Terminate System Process", command=self.terminate_system_process, style="TerminateSystem.TButton")
        terminate_system_button.pack(pady=10, fill='x')
        ToolTip(terminate_system_button, text="Terminate the system process (broken)", bootstyle=("red", "yellow"))

                
                        
        # Create the right panel
        right_panel = Frame(main_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Create the conversation frame
        conversation_frame = Frame(right_panel)
        conversation_frame.pack(fill='both', expand=True)

        # Create the conversation text widget
        self.conversation_text = Text(conversation_frame, wrap='word', width=60, height=20)
        self.conversation_text.pack(side='left', fill='both', expand=True)
        self.conversation_text.tag_configure('output', foreground='blue')
        self.conversation_text.tag_configure('code', background='#f0f0f0', font=('Courier', 10))

        # Create a scrollbar for the conversation text widget
        scrollbar = Scrollbar(conversation_frame)
        scrollbar.pack(side='right', fill='y')

        self.conversation_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.conversation_text.yview)


        # Create the input frame
        input_frame = Frame(right_panel)
        input_frame.pack(fill='x')

        # Create the user input entry widget
        self.user_input = Entry(input_frame, width=60)
        self.user_input.pack(side='left', fill='x', expand=True)
        self.user_input.bind("<Return>", self.send_command)


        # Create the send button
        send_button = Button(input_frame, text="Send", command=self.send_command, bootstyle="success")
        send_button.pack(side='left')


        # Create the settings frame
        settings_frame = Frame(settings_tab, padding=10)
        settings_frame.pack(fill='both', expand=True)


        # Create the LLM Web Browser toggle button
        llm_web_browser_label = Label(settings_frame, text="OS Mode (Enables Web Browser):")
        llm_web_browser_label.pack(pady=10)

        self.llm_web_browser_toggle = Checkbutton(
            settings_frame,
            variable=self.llm_web_browser_enabled,
            command=self.toggle_llm_web_browser,
            bootstyle="success-round-toggle"
        )
        self.llm_web_browser_toggle.pack(pady=10)

        # Create the temperature label and meter
        temperature_label = Label(settings_frame, text="Temperature:", bootstyle="info")
        temperature_label.pack(pady=10)

        self.temperature_meter = Meter(
            settings_frame,
            metersize=180,
            padding=20,
            amounttotal=100,
            amountused=int(self.oracle_interpreter.interpreter.llm.temperature * 100),
            metertype="semi",
            subtext="Temperature",
            interactive=True,
            bootstyle="info",
            stripethickness=10
        )
        self.temperature_meter.pack(pady=10)
        ToolTip(self.temperature_meter, text="Adjust the temperature of the selected LLM/API", bootstyle="info")


        # Create the max_tokens label and meter
        max_tokens_label = Label(settings_frame, text="Max Tokens:", bootstyle="info")
        max_tokens_label.pack(pady=10)

        self.max_tokens_meter = Meter(
            settings_frame,
            metersize=180,
            padding=20,
            amounttotal=3500,
            amountused=self.oracle_interpreter.interpreter.llm.max_tokens,
            metertype="semi",
            subtext="Max Tokens",
            interactive=True,
            bootstyle="info",
            stripethickness=10
        )
        self.max_tokens_meter.pack(pady=10)
        ToolTip(self.max_tokens_meter, text="Adjust the maximum number of tokens for the selected LLM/API", bootstyle="info")


        # Create the API frame
        api_frame = Frame(api_tab, padding=10)
        api_frame.pack(fill='both', expand=True)

        # Create the provider label and radio buttons
        provider_label = Label(api_frame, text="LLM Provider:")
        provider_label.pack(pady=5)

        self.provider_var = tk.StringVar(value="OpenAI")

        openai_toggle = tk.Radiobutton(api_frame, text="OpenAI", variable=self.provider_var, value="OpenAI", command=self.update_api_key_entry)
        openai_toggle.pack(pady=5)

        anthropic_toggle = tk.Radiobutton(api_frame, text="Anthropic", variable=self.provider_var, value="Anthropic", command=self.update_api_key_entry)
        anthropic_toggle.pack(pady=5)

        anthropic_haiku_toggle = tk.Radiobutton(api_frame, text="Anthropic-Haiku", variable=self.provider_var, value="Anthropic-Haiku", command=self.update_api_key_entry)
        anthropic_haiku_toggle.pack(pady=5)


        # Create the API key label and entry widget
        api_key_label = Label(api_frame, text="API Key:")
        api_key_label.pack(pady=5)

        self.api_key_entry = Entry(api_frame, show="*")
        self.api_key_entry.pack(pady=5)


        # Create the save API key button
        save_api_key_button = Button(api_frame, text="Save API Key", command=self.save_api_key)
        save_api_key_button.pack(pady=5)

        # Create the confirm API change button
        confirm_button = Button(api_frame, text="Confirm API Change", command=self.confirm_api_change)
        confirm_button.pack(pady=10)



        # Create a frame for the Floodgauge and its labels
        floodgauge_frame = Frame(self.canvas)
        floodgauge_frame.pack(side=BOTTOM, anchor=SW, padx=10, pady=10)

        # Add the "Processing..." label to the frame
        self.processing_label = Label(floodgauge_frame, text="Processing...", bootstyle="warning")
        self.processing_label.pack(side=TOP)

        # Create a custom style for the Floodgauge widget
        self.floodgauge_style = Style()
        self.floodgauge_style.configure("custom.Horizontal.TProgressbar",
                                        background="#00FF41",  # Matrix green color for the active fill
                                        troughcolor="#003B00",  # Dark green color for the inactive background
                                        bordercolor=self.floodgauge_style.colors.bg,
                                        thickness=10)

        # Add the Floodgauge widget to the frame with custom style
        self.floodgauge = Floodgauge(floodgauge_frame, bootstyle=INFO, length=100, mode='determinate', style="custom.Horizontal.TProgressbar")
        self.floodgauge.pack(side=TOP)

        # Add the status label to the frame
        self.status_label = Label(floodgauge_frame, text="Inactive", foreground="red")
        self.status_label.pack(side=TOP)

        # Initialize the terminal output and thread
        self.terminal_output = ""
        self.terminal_thread = threading.Thread(target=self.capture_terminal_output)
        self.terminal_thread.daemon = True
        self.terminal_thread.start()

        # Initialize the Floodgauge animation variables
        self.floodgauge_animation_thread = None
        self.floodgauge_animation_running = False




        self.root.mainloop()




    def toggle_llm_web_browser(self):
        if self.llm_web_browser_enabled.get():
            # Enable the LLM Web Browser feature
            self.oracle_interpreter.enable_llm_web_browser()
        else:
            # Disable the LLM Web Browser feature
            self.oracle_interpreter.disable_llm_web_browser()
        
        # Update the system message to reflect the current state of the feature
        self.oracle_interpreter.update_system_message()
    
    def save_conversation(self):
        conversation = self.conversation_text.get("1.0", tk.END).strip()
        conversation_pairs = self.extract_conversation_pairs(conversation)

        if conversation_pairs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logs_folder = "oracle_logs"
            os.makedirs(logs_folder, exist_ok=True)

            log_file = os.path.join(logs_folder, f"dir_log_{timestamp}.jsonl")
            with open(log_file, "w") as f:
                for pair in conversation_pairs:
                    f.write(json.dumps(pair) + "\n")

            messagebox.showinfo("Conversation Saved", f"The conversation has been saved to {log_file}")
        else:
            messagebox.showwarning("No Conversation", "There is no conversation to save.")

    def extract_conversation_pairs(self, conversation):
        pairs = []
        lines = conversation.split("\n")
        user_message = ""
        bot_response = ""
        in_bot_response = False

        for line in lines:
            if line.startswith("User: "):
                if user_message and bot_response:
                    pairs.append({"user_message": user_message, "bot_response": bot_response})
                    user_message = ""
                    bot_response = ""
                    in_bot_response = False
                user_message = line[6:].strip()
            elif line.startswith("Oracle: "):
                in_bot_response = True
                bot_response += line[8:].strip() + "\n"
            elif in_bot_response:
                bot_response += line.strip() + "\n"

        if user_message and bot_response:
            pairs.append({"user_message": user_message, "bot_response": bot_response.strip()})

        return pairs

    def create_session_log_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_folder = "oracle_logs"
        os.makedirs(logs_folder, exist_ok=True)

        log_file = os.path.join(logs_folder, f"session_{timestamp}.jsonl")
        return log_file

    def confirm_api_change(self):
        """
        Confirm the change of the LLM provider and update the settings.
        """
        provider = self.provider_var.get()
        self.process_command(f"!switch_provider {provider}")
        self.flash_window()
        self.play_sound_effect()
        self.update_settings()


    def update_settings(self):
        """
        Update the temperature and max_tokens settings based on the values from the meters.
        """
        temperature = self.temperature_meter.amountusedvar.get() / 100.0
        max_tokens = int(self.max_tokens_meter.amountusedvar.get())

        if self.oracle_interpreter.interpreter.llm.model_name == self.oracle_interpreter.OPENAI_MODEL_NAME:
            self.oracle_interpreter.interpreter.llm.temperature = temperature
            self.oracle_interpreter.interpreter.llm.max_tokens = max_tokens
        elif self.oracle_interpreter.interpreter.llm.model_name in [self.oracle_interpreter.ANTHROPIC_MODEL_NAME, self.oracle_interpreter.ANTHROPIC_MODEL_NAME_HAIKU]:
            normalized_temperature = temperature * 0.9 + 0.1
            self.oracle_interpreter.interpreter.llm.temperature = normalized_temperature
            self.oracle_interpreter.interpreter.llm.max_tokens = min(max(max_tokens, 1), 8192)


    def resize_background_image(self, event):
        """
        Resize the background image when the window is resized.
        
        Args:
            event (tkinter.Event): The event object containing information about the resize event.
        """
        window_width = event.width
        window_height = event.height

        resized_bg_image = self.bg_image.resize((window_width, window_height), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(resized_bg_image)

        self.canvas.delete('all')
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor='nw')
    
    # Broken    
    def flash_window(self):
        """
        Flash the window with a green color to indicate a successful action.
        """
        original_color = self.root.cget('bg')
        self.root.configure(bg='#80ff80')
        self.root.update()
        time.sleep(0.3)
        self.root.configure(bg=original_color)
        self.root.update()
    
    
    # The world is veiled in darkness.
    # The wind stops, the sea is wild, the earth begins to rot.
    # The people wait, their only hope, a prophecy...
    def play_sound_effect(self):
        """
        Play a sound effect using Pygame.
        """
        pygame.mixer.init()
        sound_file = "se_1.mp3"
        sound_path = os.path.join(os.path.dirname(__file__), sound_file)
        sound = pygame.mixer.Sound(sound_path)
        sound.play()


    def send_command(self, event=None):
        """
        Send the user's command to the Oracle Interpreter for processing.
        
        Args:
            event (tkinter.Event, optional): The event object containing information about the event that triggered the command. Defaults to None.
        """
        command = self.user_input.get()
        self.user_input.delete(0, 'end')
        self.conversation_text.insert('end', "User: " + command + '\n')

        threading.Thread(target=self.process_command, args=(command,)).start()

    # Correct method for closing the GUI. 
    def stop_oracle_interpreter(self):
        """
        Stop the Oracle Interpreter and close the GUI.
        """
        self.controller.stop()
        self.queue.put("GUI closed")
        self.stop_event.set()  # Set the stop event to signal the capture_terminal_output thread to stop
        self.root.quit()
        self.root.destroy()
            
    # Broke 
    def pause_oracle_interpreter(self):
        """
        Pause the Oracle Interpreter.
        """
        self.controller.pause()


    # Guess what?
    def start_or_resume_oracle_interpreter(self):
        """
        Start or resume the Oracle Interpreter.
        """
        if self.controller.process is None:
            self.controller.start()
        else:
            self.controller.resume()



    def open_antikythera_directory(self):
        """
        Open the Antikythera directory in the file explorer.
        """
        if os.path.exists("antikythera"):
            os.startfile("antikythera")
        else:
            messagebox.showwarning("Directory Not Found", "The 'antikythera' directory does not exist.")


    def open_alexandria_directory(self):
        """
        Open the Alexandria directory in the file explorer.
        """
        if os.path.exists("alexandria"):
            os.startfile("alexandria")
        else:
            messagebox.showwarning("Directory Not Found", "The 'alexandria' directory does not exist.")

    def open_aetherion_directory(self):
        if os.path.exists(self.aetherion_directory):
            os.startfile(self.aetherion_directory)
        else:
            messagebox.showwarning("Directory Not Found", f"The '{self.aetherion_directory}' directory does not exist.")

    def open_athenium_directory(self):
        if os.path.exists(self.athenium_directory):
            os.startfile(self.athenium_directory)
        else:
            messagebox.showwarning("Directory Not Found", f"The '{self.athenium_directory}' directory does not exist.")

    def open_acheron_directory(self):
        if os.path.exists(self.acheron_directory):
            os.startfile(self.acheron_directory)
        else:
            messagebox.showwarning("Directory Not Found", f"The '{self.acheron_directory}' directory does not exist.")

    def open_open_interpreter_directory(self):
        open_interpreter_directory = "Open Interpreter/*"
        if os.path.exists(open_interpreter_directory):
            os.startfile(open_interpreter_directory)
        else:
            messagebox.showwarning("Directory Not Found", f"The '{open_interpreter_directory}' directory does not exist.")

    def open_logs_folder(self):
        logs_folder = "oracle_logs"
        if os.path.exists(logs_folder):
            subprocess.Popen(f'explorer "{logs_folder}"')

    def terminate_system_process(self):
        messagebox.showinfo("System Process Termination", "System process termination is currently unavailable. If you have an emergency, manually terminate the process.")

    def process_command(self, command):
        """
        Process the user's command and update the GUI accordingly.
        
        Args:
            command (str): The command entered by the user.
        """
        if command.startswith("!switch_provider"):
            provider = command.split(" ")[1]
            if provider == "OpenAI":
                self.oracle_interpreter.interpreter.llm.model_name = self.oracle_interpreter.OPENAI_MODEL_NAME
            elif provider == "Anthropic":
                self.oracle_interpreter.interpreter.llm.model_name = self.oracle_interpreter.ANTHROPIC_MODEL_NAME
            elif provider == "Anthropic-Haiku":
                self.oracle_interpreter.interpreter.llm.model_name = self.oracle_interpreter.ANTHROPIC_MODEL_NAME_HAIKU
        else:
            self.start_floodgauge_animation()  # Start the Floodgauge animation
            self.update_status_label("Active", "green")  # Update status label to "Active" in green
            response = self.oracle_interpreter.chat(command)
            self.stop_floodgauge_animation()  # Stop the Floodgauge animation
            self.update_status_label("Inactive", "red")  # Update status label to "Inactive" in red
            self.conversation_text.insert('end', "Oracle: " + response + '\n')
            self.conversation_text.see('end')
            self.root.update()


    def update_status_label(self, text, color):
        """
        Update the status label with the given text and color.
        
        Args:
            text (str): The text to display in the status label.
            color (str): The color of the status label text.
        """
        self.status_label.configure(text=text, foreground=color)
        

    
    def update_conversation_text(self, formatted_output):
        self.conversation_text.insert('end', formatted_output)
        self.conversation_text.see('end')
       
        
    # My dear Dr. Moog, call that a patch cable
    def capture_terminal_output(self):
        """
        Capture the terminal output from the Oracle Interpreter and display it in the conversation text widget.
        """
        process = subprocess.Popen(["python", "oracle.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

        conversation_buffer = []
        user_message = ""
        bot_response = ""

        while not self.stop_event.is_set():
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                if not self.is_unwanted_message(output):
                    if output.startswith("User: "):
                        user_message = output[6:].strip()
                        conversation_buffer.append({"role": "user", "content": user_message})
                    elif output.startswith("Oracle: "):
                        bot_response += output[8:].strip() + "\n"
                    else:
                        bot_response += output.strip() + "\n"

                    formatted_output = self.format_output(output)
                    self.root.after(0, self.update_conversation_text, formatted_output)

            else:
                if user_message and bot_response:
                    conversation_buffer.append({"role": "assistant", "content": bot_response.strip()})
                    self.log_conversation(conversation_buffer)
                    user_message = ""
                    bot_response = ""
                    conversation_buffer = []
                time.sleep(0.1)

        self.root.after(0, self.update_status_label, "Inactive", "red")  # Update status label to "Inactive" in red
        
    # Ridiculous, Mr. Data
    def log_conversation(self, conversation_buffer):
        with open(self.session_log_file, "a") as f:
            for message in conversation_buffer:
                f.write(json.dumps(message) + "\n")

    # And it wouldn't be complete without analogue filters
    def is_unwanted_message(self, message):
        """
        Check if the given message is an unwanted message that should be filtered out.
        
        Args:
            message (str): The message to check.
        
        Returns:
            bool: True if the message is unwanted, False otherwise.
        """
        unwanted_patterns = [
            r"UserWarning: Field",
            r"You may be able to resolve this warning",
            r"pygame",
            r"Hello from the pygame community",
            r"warnings.warn\(",
            r"\[\d+;\d+;\d+m.*\[0m"
        ]
        for pattern in unwanted_patterns:
            if re.search(pattern, message):
                return True
        return False

    # Chocolate fountain style. Or perhaps a bucket-brigade discrete-time analogue delay line?
    def slow_type(self, text, tag, delay):
        """
        Display the given text in the conversation text widget with a typewriter effect.
        
        Args:
            text (str): The text to display.
            tag (str): The tag to apply to the text.
            delay (float): The delay between each character.
        """
        for char in text:
            self.conversation_text.insert(tk.END, char, tag)
            self.conversation_text.see(tk.END)
            self.conversation_text.update_idletasks()
            time.sleep(delay)

    # We sign post. Call that semiotic engineering
    def format_output(self, line):
        """
        Format the given line of output based on its content.
        
        Args:
            line (str): The line of output to format.
        
        Returns:
            str: The formatted output.
        """
        if line.startswith("User: "):
            return f"\n\n{line}"
        elif line.startswith("Oracle: "):
            return f"\n{line}"
        elif line.startswith("```"):
            lexer = get_lexer_by_name("python", stripall=True)
            formatter = HtmlFormatter(style='colorful')
            highlighted_code = highlight(line[3:-3], lexer, formatter)
            return f"\n{highlighted_code}\n"
        else:
            return line


    # Clavicula Routus
    def update_api_key_entry(self):
        """
        Update the API key entry widget based on the selected provider.
        """
        provider = self.provider_var.get()
        if provider == "OpenAI":
            self.api_key_entry.delete(0, 'end')
            self.api_key_entry.insert(0, os.environ.get("OPENAI_API_KEY", ""))
        elif provider in ["Anthropic", "Anthropic-Haiku"]:
            self.api_key_entry.delete(0, 'end')
            self.api_key_entry.insert(0, os.environ.get("ANTHROPIC_API_KEY", ""))

    # Please enter pass code
    def save_api_key(self):
        """
        Save the API key based on the selected provider.
        """
        provider = self.provider_var.get()
        api_key = self.api_key_entry.get()

        if provider == "OpenAI":
            openai.api_key = api_key
            os.environ["OPENAI_API_KEY"] = api_key
            messagebox.showinfo("API Key Saved", "OpenAI API key has been saved.")
        elif provider in ["Anthropic", "Anthropic-Haiku"]:
            self.oracle_interpreter.anthropic_client = anthropic.Client(api_key=api_key)
            os.environ["ANTHROPIC_API_KEY"] = api_key
            messagebox.showinfo("API Key Saved", "Anthropic API key has been saved.")

    # Nothing to see here, Mr. Wario
    def iterate_colors(self):
        """
        Iterate through different colors for the Floodgauge widget.
        """
        theme_colors = [self.floodgauge_style.colors.primary,
                        self.floodgauge_style.colors.secondary,
                        self.floodgauge_style.colors.success,
                        self.floodgauge_style.colors.info,
                        self.floodgauge_style.colors.warning,
                        self.floodgauge_style.colors.danger]

        while True:
            for color in theme_colors:
                for i in range(100):
                    progress_color = self.floodgauge_style.colors.update_hsv(color, vd=i/100)
                    self.floodgauge.configure(bootstyle=(INFO, progress_color))
                    time.sleep(0.01)  # Adjust the delay to control the speed of iteration

    # Its the little things in life...
    def start_floodgauge_animation(self):
        """
        Start the Floodgauge animation.
        """
        if not self.floodgauge_animation_running:
            self.floodgauge_animation_running = True
            self.floodgauge_animation_thread = threading.Thread(target=self.animate_floodgauge)
            self.floodgauge_animation_thread.start()

    # ...Till death do us part...
    def stop_floodgauge_animation(self):
        """
        Stop the Floodgauge animation.
        """
        self.floodgauge_animation_running = False
        if self.floodgauge_animation_thread is not None:
            self.floodgauge_animation_thread.join()

    # Let us cling together
    def animate_floodgauge(self):
        """
        Animate the Floodgauge widget to indicate processing progress.
        """
        while self.floodgauge_animation_running:
            for value in range(0, 101, 10):
                if not self.floodgauge_animation_running:
                    break
                self.floodgauge['value'] = value
                self.root.update()
                time.sleep(0.1)
            self.floodgauge['value'] = 0
            self.root.update()