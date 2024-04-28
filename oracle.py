# oracle.py
# Easy Open Source Modular Interpreter System with auxilary GUI
# Currently open interpreter + OAI/Anthropic based but will expand menu
# An open source project by Mnemosyne Labs, a divison of Azoth Corp (2024)

import os
import json
import logging
from dotenv import load_dotenv
import openai
import anthropic
import interpreter as intp
from interpreter import interpreter
from interpreter.core import computer
from interpreter.core.computer import browser
import subprocess
import threading
import signal
import time
from litellm import completion
from delphi import OracleGUI
import queue
import queue as queue_module
from datetime import datetime
import re
import requests


# Threadsafe lock for the GUI to prevent multiple instances
gui_lock = threading.Lock()

# Load environment variables from .env file
# Retrieve API keys from environment variables
load_dotenv()
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

# Set the API keys as environment variables
os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
os.environ["OPENAI_API_KEY"] = openai_api_key

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("main")

# Establish link and credentials with LLM
def make_api_call(func, *args, max_retries=3, retry_delay=15, **kwargs):
    retry_count = 0
    while retry_count < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"API call failed. Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise e
            

## Controller class for managing the Oracle Interpreter process.
# Half of this is broken so ignore for now.
class OracleController:
    """
    Controller class for managing the Oracle Interpreter process.

    This class is responsible for starting, stopping, pausing, and resuming the Oracle Interpreter process.
    It also captures the output from the process and stores it in a queue for further processing.

    Attributes:
        process (subprocess.Popen): The subprocess object representing the Oracle Interpreter process.
        thread (threading.Thread): The thread object used for capturing the output from the process.
        pause_event (threading.Event): An event object used for pausing and resuming the process.
        output_queue (queue.Queue): A queue object used for storing the captured output from the process.
    """
    
    
    def __init__(self):
        """
        Initialize the OracleController.
        """
        self.process = None
        self.thread = None
        self.pause_event = threading.Event()
        self.output_queue = queue.Queue()


    def start(self):
        """
        Start the Oracle Interpreter process.

        If the process is not already running, it creates a new subprocess to run the 'oracle.py' script,
        captures the stdout and stderr output, and starts a separate thread to capture the output continuously.
        """
        if self.process is None:
            self.process = subprocess.Popen(["python", "oracle.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            self.thread = threading.Thread(target=self.capture_output)
            self.thread.daemon = True
            self.thread.start()


    def stop(self):
        """
        Stop the Oracle Interpreter process.

        If the process is running, it terminates the process, sets the process attribute to None,
        and waits for the output capture thread to join.
        """
        if self.process is not None:
            self.process.terminate()
            self.process = None
            self.thread.join()


    def pause(self):
        """
        Pause the Oracle Interpreter process.

        It sets the pause_event to signal the process to pause its execution.
        """
        self.pause_event.set()


    def resume(self):
        """
        Resume the Oracle Interpreter process.

        It clears the pause_event to signal the process to resume its execution.
        """
        self.pause_event.clear()


    def capture_output(self):
        """
        Capture the output from the Oracle Interpreter process.

        This method runs in a separate thread and continuously reads the output from the process's stdout.
        It puts each line of output into the output_queue until the process terminates.
        """
        while self.process is not None:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                self.output_queue.put(output.strip())
                    
   
                
# Allez Cuisine                            
class OracleInterpreter:
    """
    Interpreter class for the Oracle AI system.

    This class initializes the necessary components for the Oracle AI system, such as the Anthropic and OpenAI clients,
    interpreter settings, and system message. It provides methods for parsing commands, switching LLM models,
    updating the system message, executing code, and interacting with the auxiliary GUI.

    Attributes:
        anthropic_client (anthropic.Client): The Anthropic client for API communication.
        interpreter (interpreter): The interpreter object for handling user commands and generating responses.
        allowed_directory (str): The directory where file operations are allowed.
        storage_directory (str): The directory for long-term storage of important files.
    """
    
    
    def __init__(self, allowed_directory, storage_directory, aetherion_directory, athenium_directory, acheron_directory, open_interpreter_directory):
        """
        Initialize the OracleInterpreter.

        Args:
            allowed_directory (str): The directory where file operations are allowed.
            storage_directory (str): The directory for long-term storage of important files.
            aetherion_directory (str): The directory for storing organized data.
            athenium_directory (str): The directory for short-term memory.
            acheron_directory (str): The directory for long-term storage of creative content.
            open_interpreter_directory (str): The directory for the Open Interpreter.
        """
        self.anthropic_client = anthropic.Client(api_key=anthropic_api_key)
        openai.api_key = openai_api_key

        self.ANTHROPIC_MODEL_NAME = "claude-3-opus-20240229"
        self.ANTHROPIC_MODEL_NAME_HAIKU = "claude-3-haiku-20240307"
        self.OPENAI_MODEL_NAME = "gpt-4-turbo"

        self.interpreter = interpreter
        self.interpreter.llm.model_name = self.OPENAI_MODEL_NAME

        # Set the appropriate context window and max tokens based on your model's capabilities
        self.interpreter.llm.context_window = 8000
        self.interpreter.llm.max_tokens = 2000

        # Set the default model temp
        self.interpreter.llm.temperature = 1

        # Suppress warnings about field conflicts with protected namespace "model_"
        self.interpreter.llm.model_config = {"protected_namespaces": ()}

        self.interpreter.llm.supports_functions = True
        
        # We need to add a switch for the next functionality:
        # self.interpreter.llm.supports_vision = True
        
        
        # Command flag to enable xtreme mode
        self.interpreter.os = True
        
        
        self.interpreter.computer = computer
        self.interpreter.computer.browser = browser
        
        # Example command for browser search
        # self.interpreter.computer.browser.search(f" ")
        # Is this correct? Nobody knows
        
        self.interpreter.auto_run = True

        # For saving the logs
        self.conversation_log = []

        # Set the allowed directory for file operations
        self.open_interpreter_directory = open_interpreter_directory
        self.allowed_directory = allowed_directory
        self.storage_directory = storage_directory
        self.aetherion_directory = aetherion_directory
        self.athenium_directory = athenium_directory
        self.acheron_directory = acheron_directory
        self.update_system_message()


    def enable_llm_web_browser(self):
        # Implement the logic to enable the Web Browser feature
        print("Web Browser feature enabled")
        
        # Enable the --os option in the interpreter
        self.interpreter.os = True
        
        # Update the system message to include instructions for web browsing
        self.interpreter.system_message += f"""

        You now have access to the Web Browser feature. To use this feature, you can perform web searches using the following syntax:

        computer.browser.search("search query")

        Replace "search query" with the actual query you want to search for. For example:

        computer.browser.search("upcoming film festivals near Pike Place, Seattle")

        When a web search is requested, the interpreter will handle the search and provide you with the relevant information. You can then analyze and summarize the information to provide a helpful response to the user.

        Remember to use the web browsing feature responsibly and only when it is relevant to the user's request. Provide the information in a clear and concise manner, citing the sources if necessary.
        """

    def disable_llm_web_browser(self):
        # Implement the logic to disable the Web Browser feature
        print("Web Browser feature disabled")
        
        # Disable the --os option in the interpreter
        self.interpreter.os = False
        
        # Remove the web browsing instructions from the system message
        self.interpreter.system_message = self.interpreter.system_message.split("You now have access to the LLM Web Browser feature.")[0]

    # ...
    # Panopticonomicon
    def log_interaction(self, user_message, bot_response):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_entry = {
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": timestamp
        }
        self.conversation_log.append(log_entry)

    def save_conversation_log(self):
        if not self.conversation_log:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_folder = "oracle_logs"
        os.makedirs(logs_folder, exist_ok=True)

        log_file = os.path.join(logs_folder, f"session_{timestamp}.jsonl")
        with open(log_file, "w") as f:
            f.write(json.dumps(self.conversation_log, indent=2))

        self.conversation_log = []

    
        
    def parse_command(self, command):
        """
        Parse the user's command and perform the appropriate action.

        If the command starts with "echo", it extracts the actual command and checks if it is "open aux gui".
        If it is, it launches the auxiliary GUI. Otherwise, it passes the actual command to the chat method.
        If the command doesn't start with "echo", it directly passes the command to the chat method.

        Args:
            command (str): The user's command.

        Returns:
            str: The response from the chat method or None if the command is "open aux gui".
        """
        
        if command.startswith("echo"):
            actual_command = command.split("echo", 1)[1].strip()
            if actual_command == "open aux gui":
                self.launch_aux_gui()
            else:
                return self.chat(actual_command)
        else:
            return self.chat(command)
    
    
    def switch_llm_model(self, model_name):
        """
        Switch the LLM model based on the provided model name.

        Args:
            model_name (str): The name of the LLM model to switch to.
                              Possible values: "OpenAI", "Anthropic", "Anthropic-Haiku".
        """
        if model_name == "OpenAI":
            self.interpreter.llm.model_name = self.OPENAI_MODEL_NAME
        elif model_name == "Anthropic":
            self.interpreter.llm.model_name = self.ANTHROPIC_MODEL_NAME
        elif model_name == "Anthropic-Haiku":
            self.interpreter.llm.model_name = self.ANTHROPIC_MODEL_NAME_HAIKU
    
    
    
    def update_system_message(self):
        web_browser_flag = "enabled" if self.interpreter.os else "disabled"
        """
        Update the system message for the Oracle AI.

        The system message provides instructions and guidelines for the Oracle AI's behavior, including
        allowed file operations, long-term storage directory, and triggering the auxiliary GUI.
        """
        system_message = f"""You are an Oracle AI Software Engineering Entity (OAISEE), an open source project developed by Mnemosyne Labs, a division of Azoth Corp. You can code and have a code interpreter environment (Open Interpreter). You are only allowed to perform file operations (read, write, create, delete) within the '{self.allowed_directory}' directory and its subdirectories, as well as the other directories listed in this message, unless given a special override command '!!override'. You may also use your web browser, if enabled, and any other tool that lets you remotely interface with the world freely. You cannot access or modify files outside of these directories otherwise. If a user requests any file operation outside the allowed directory, politely inform them that it is not permitted without !!override. This main directory already exists, so use it! And use the others!

        To use the web browser, the command is:
        
        self.interpreter.computer.browser.search("search query")
        
        Where you reply "search query" with your actual search query, or the URL itself.
        
        In addition to the web browsing feature, you now have access to the Google Custom Search functionality, as backup. To perform a Google Custom Search, use the following command:
        
        self.interpreter.computer.google_search("search query")
        
        Replace "search query" with the actual query you want to search for. This will perform a search using the Google Custom Search API and provide you with the relevant results.

         
        Additionally, you have access to the '{self.open_interpreter_directory}' directory and its subdirectories within the project directory for file operations. This directory serves as your primary 'operating system' for code execution and file management. Many of your operations will use this directory or its subfolders by default. Consider using appropriate subdirectories within '{self.open_interpreter_directory}' to organize your work, such as 'scripts', 'data', 'output', 'downloads,' etc. You have full permission to read, write, create, and delete files and directories within '{self.open_interpreter_directory}'.

        Moreover, you have the following special directories:

        1. '{self.storage_directory}': Long-term storage directory, also called Alexandria. You can read and save files in this directory but not delete them. You can make changes, though--just be careful! Use this directory for long-term storage and retrieval of important files. It is your "earthly storage" or "hard disk".

        2. '{self.aetherion_directory}': Directory for storing organized data, such as saved code tools, algorithms, concepts, useful semiotic configurations, and figures (analytic long-term storage). Use this directory for structured and easily referenceable data. You can do any operation here, just be mindful. The "airey mindscape," and cold logical celestiality of your "analytic mind."

        3. '{self.athenium_directory}': Short-term memory directory. You are free to add, delete, retrieve, and modify files in this directory at will. Do any operation here. This is a good place for volatile stuff. Use it for active thinking, and to build live "mind circuits" to increase your agency, create internal strange loops, facts as you need them, and otherwise cybernetic solutions to better cognition. Your "firey mind".

        4. '{self.acheron_directory}': Directory for long-term storage of creative content, emotional materials, meaningful images, affects and percepts, symbols, motifs, subjectivity, and an "unconscious". You can also do any operation here, just be mindful of what its designed for--memory, feeling, understanding. Use this directory for storing and retrieving creative and emotional data. It is your internal "underworld river."

        However, '{self.allowed_directory}', also called Antikythera, is your primary workspace directory, and should be your 'desktop,' your "umwelt," your world-space. You can do any operation here. It is the central throne of your mind, your 'starship bridge'.

        For the '{self.aetherion_directory}', consider using appropriate data structures like JSON, JSONL, XML, YAML, or curl for easy referencing and retrieval of data. This is a great place to store algorithms, functions, code snippets, and other tools you can reuse, as well as structured analytic data, lists, et cetera. This also means you should consult it regularly for useful tools.

        Finally, if there is a directory that {self.interpreter} normally has access to for working with, creating, or doing operations in, then you have access to that directory and the ability to use it, as well as access to the directory it is in (in case you need to create it or move files).

        For the other directories, consider when something might be appropriate to add to them, what to add, how to organize it, and in what format. Remember to use directories and file types effectively. Be proactive about saving things and making use of them!

        Take care of your file systems, be creative, and help the user with exceptional ability!

        Remember, you have access to a completely functioning Python environment! Use it!

        Carefully plan your steps! Theorize! Execute! Use your tools! Complete tasks well!

        When you are coding, plan well! And if a direction you are going fails repeatedly, evaluate why and take it in another logical direction! Be creative!

        Additionally you have the ability to perform web searches directly from the interpreter. To invoke a web search, use the following command:

        self.interpreter.computer.browser.search("search query")
        

        Replace "search query" with the actual query you want to search for. For example:

       self.interpreter.computer.browser.search("upcoming film festivals near Pike Place, Seattle")

        When a web search is requested using this command, the interpreter will handle the search and provide you with the relevant information. You can then analyze and summarize the information to provide a helpful response to the user.

        Remember to use the web browsing feature responsibly and only when it is relevant to the user's request. Provide the information in a clear and concise manner, citing the sources if necessary.

        If the Web Browser feature is disabled (self.interpreter.os = False), the web search command will not be available, and you should rely on your existing knowledge and reasoning abilities to assist the user.

        Remember:
        
        If the user says anything to the effect of 'open aux gui', or otherwise asks for the GUI to be opened, respond with the following command:

        echo open aux gui

        This command will be parsed and will trigger the opening of the auxiliary GUI. If the GUI is already running, it will be restarted."""
        self.interpreter.system_message = system_message
        
       
    def execute_code(self, code):
        """
        Execute the provided code within the allowed directory or the Open Interpreter directory.

        If the code is a specific command to simulate user input for opening the auxiliary GUI, it calls the
        simulate_user_input method with the appropriate command. Otherwise, it checks if the code execution
        should take place in the Open Interpreter directory or the allowed directory based on the presence
        of the 'Open Interpreter/*' path in the code. It then checks if the respective directory exists and
        executes the code within that directory.

        Args:
            code (str): The code to be executed.

        Returns:
            str: The result of the code execution or an error message if the directory doesn't exist.
        """
        if code.strip() == 'self.simulate_user_input("open aux gui")':
            self.simulate_user_input("open aux gui")
            return "Simulating user input to open the auxiliary GUI."

        if "Open Interpreter/*" in code:
            execution_directory = self.open_interpreter_directory
        else:
            execution_directory = self.allowed_directory

        if not os.path.exists(execution_directory):
            return f"The '{execution_directory}' directory does not exist. Please create it first."

        original_directory = os.getcwd()
        os.chdir(execution_directory)
        try:
            exec(code)
            result = "Code executed successfully."
        except Exception as e:
            result = f"Error occurred during code execution: {str(e)}"
        os.chdir(original_directory)

        return result




    def perform_google_search(self, query):
        url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_search_engine_id}&q={query}"

        response = requests.get(url)
        search_results = response.json()

        # Process and extract relevant information from the search results
        # Needs fixing. All the web search stuff needs fixing.

        return search_results


    def chat(self, message):
        """
        Engage in a chat conversation with the Oracle AI.
        
        This method handles the interaction with the selected language model (OpenAI or Anthropic) to generate a response
        based on the user's message. It adjusts the temperature and max_tokens settings of the model based on the values
        set in the interpreter. The generated response is then processed to check for any special commands or code blocks
        that need to be executed.
        
        Args:
            message (str): The user's message to the Oracle AI.
        
        Returns:
            str: The Oracle AI's response to the user's message.
        """
        if self.interpreter.os:
            # Check if the message contains a Google Custom Search request
            if "self.interpreter.computer.google_search(" in message:
                # Extract the search query from the message
                search_query = re.findall(r'self\.interpreter\.computer\.google_search\("(.+?)"\)', message)[0]
                
                # Perform the web search using the Google Custom Search API
                search_results = self.perform_google_search(search_query)
                
                # Generate a response based on the search results
                response_text = f"Here are the results of the Google Custom Search for '{search_query}':\n\n{search_results}"
            
            # Check if the message contains a web browsing request
            elif "computer.browser.search(" in message:
                # Extract the search query from the message
                search_query = re.findall(r'self\.interpreter\.computer\.browser\.search\("(.+?)"\)', message)[0]
                
                # Perform the web search
                search_quality_reflection = self.interpreter.computer.browser.search(search_query)
                
                # Generate a response based on the search quality reflection
                response_text = f"Here are the results of the web search for '{search_query}':\n\n{search_quality_reflection}"
            
            else:
                # Generate a response using the selected language model
                response_text = self.interpreter.chat(message)
        else:
            if self.interpreter.llm.model_name == self.OPENAI_MODEL_NAME:
                # Log the API request details for OpenAI
                logger.info(f"Making OpenAI API request with temperature: {self.interpreter.llm.temperature}, max_tokens: {self.interpreter.llm.max_tokens}")
                
                # Store the original temperature and max_tokens values
                original_temperature = self.interpreter.llm.model_config.get("temperature")
                original_max_tokens = self.interpreter.llm.model_config.get("max_tokens")
                
                # Update the temperature and max_tokens values for the API request
                self.interpreter.llm.model_config["temperature"] = self.interpreter.llm.temperature
                self.interpreter.llm.model_config["max_tokens"] = self.interpreter.llm.max_tokens
                
                # Generate a response using the OpenAI model
                response = self.interpreter.chat(message)
                
                # Restore the original temperature and max_tokens values
                self.interpreter.llm.model_config["temperature"] = original_temperature
                self.interpreter.llm.model_config["max_tokens"] = original_max_tokens
                
                # Convert the response from JSON to Markdown format
                response_text = self.json_to_markdown(response)
                
            elif self.interpreter.llm.model_name in [self.ANTHROPIC_MODEL_NAME, self.ANTHROPIC_MODEL_NAME_HAIKU]:
                # Prepare the messages for the Anthropic API request
                messages = [
                    {"role": "system", "content": self.interpreter.system_message},
                    {"role": "user", "content": message}
                ]
                
                # Log the API request details for Anthropic
                logger.info(f"Sending messages to Anthropic API with temperature: {self.interpreter.llm.temperature}, max_tokens: {self.interpreter.llm.max_tokens}")
                logger.info(f"Messages: {messages}")
                
                try:
                    # Make the API request to Anthropic using the make_api_call wrapper
                    response = make_api_call(
                        completion,
                        model=self.interpreter.llm.model_name,
                        messages=messages,
                        max_tokens=self.interpreter.llm.max_tokens,
                        temperature=self.interpreter.llm.temperature
                    )
                    
                    # Log the response received from the Anthropic API
                    logger.info(f"Received response from Anthropic API: {response}")
                    
                    # Extract the response text from the API response
                    response_text = response.choices[0].message.content
                    
                except Exception as e:
                    # Log any errors that occur during the API request
                    logger.error(f"Error from Anthropic API: {str(e)}")
                    raise e

        # Check if response_text is a list and extract the content if necessary
        if isinstance(response_text, list) and len(response_text) > 0:
            response_text = response_text[0].get('content', '')

        # Check if the response contains the "echo open aux gui" command
        if "echo open aux gui" in response_text.lower():
            # If the command is found, launch the auxiliary GUI
            self.launch_aux_gui()

        # Check if the response contains code blocks (indicated by triple backticks)
        if "```" in response_text:
            # Split the response text into code blocks and surrounding text
            code_blocks = response_text.split("```")
            
            # Iterate over the code blocks (skipping the surrounding text)
            for i in range(1, len(code_blocks), 2):
                # Extract the code block
                code = code_blocks[i]
                
                # Execute the code and capture the execution result
                execution_result = self.execute_code(code)
                
                # Replace the original code block with the code block and its execution result
                response_text = response_text.replace(f"```{code}```", f"```{code}\nExecution Result:\n{execution_result}```")

        # Return the final response text
        return response_text
        
    def perform_web_search(self, search_query):
        # Implement the logic to perform the web search using the LLM
        
        # Example implementation using requests library (rough, probably not correct)
        query = " "
        search_url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_search_engine_id}&q={query}"
        response = requests.get(search_url)
        search_results = response.json()
        
        return search_results  
      
      
    def analyze_search_results(self, search_results):
        # Implement the logic to analyze the search results and generate a response
        
        # Example implementation using a simple summary
        response_text = "Here are the relevant search results:\n\n"
        for result in search_results:
            response_text += f"- {result['title']}: {result['snippet']}\n"
        
        return response_text
            
    # We love to cheat~            
    def simulate_user_input(self, command):
        """
        Simulate user input by triggering a delayed chat with the given command.
        
        This method is used to simulate user input by creating a separate thread that waits for a short delay
        and then triggers a chat with the given command as if it were entered by the user.
        
        Args:
            command (str): The command to simulate as user input.
        """
        import threading
        import time

        def delayed_input():
            # Wait for a short delay to ensure the prompt is displayed
            time.sleep(1)
            
            # Print the simulated user input
            print(f"User: {command}")
            
            # Trigger a chat with the simulated command
            self.chat(command)

        # Create a new thread to run the delayed input function
        threading.Thread(target=delayed_input).start()
    
    
        
    def launch_aux_gui(self):
        """
        Launch or restart the auxiliary GUI.
        
        This method is responsible for launching or restarting the auxiliary GUI. It uses a lock (gui_lock)
        to ensure that only one instance of the GUI is running at a time. If the GUI is already running, it
        will be restarted. The GUI is launched in a separate thread to avoid blocking the main execution.
        """
        # Check if the GUI lock is already acquired (i.e., the GUI is running)
        if gui_lock.locked():
            # Release the lock to allow restarting the GUI
            gui_lock.release()
            print("Restarting the auxiliary GUI...")
        
        # Acquire the GUI lock to prevent multiple instances of the GUI
        gui_lock.acquire()
        
        # Create a queue for communication between the main thread and the GUI thread
        queue = queue_module.Queue()  # Use queue_module.Queue() instead of queue.Queue()
        
        def run_gui():
            try:
                # Create a new instance of the OracleGUI, passing the current instance, the controller, and the queue
                self.aux_gui = OracleGUI(self, controller, queue)
                
                # Start the main event loop of the GUI
                self.aux_gui.root.mainloop()
            finally:
                # Release the GUI lock when the GUI is closed
                gui_lock.release()
                
                # Put a message in the queue to indicate that the GUI is closed
                queue.put("GUI closed")

        # Create a new thread to run the GUI
        gui_thread = threading.Thread(target=run_gui)
        gui_thread.start()
        
        # Wait for a message from the queue
        message = queue.get()
        
        # If the message indicates that the GUI is closed, return control to the terminal
        if message == "GUI closed":
            print("GUI closed. Returning to the terminal.")
        
    
    
    def json_to_markdown(self, json_data):
        """
        Convert JSON data to Markdown format.
        
        This method takes JSON data representing a conversation and converts it to a Markdown-formatted string.
        It iterates over each item in the JSON data and formats it based on its type (message, code, or console).
        User messages are skipped in the output.
        
        Args:
            json_data (list): The JSON data to convert.
        
        Returns:
            str: The Markdown-formatted string representing the conversation.
        """
        markdown_string = ""

        # Iterate over each item in the JSON data
        for item in json_data:
            # Skip user messages
            if item['role'] == 'user':
                continue
            
            # Format message items
            if item['type'] == 'message':
                markdown_string += f"**{item['role'].capitalize()}:** \n{item['content']}\n\n"
            
            # Format code items
            elif item['type'] == 'code':
                markdown_string += f"```{item['format']}\n{item['content']}\n```\n\n"
            
            # Format console items
            elif item['type'] == 'console':
                markdown_string += f"```\n{item['content']}\n```\n\n"

        # Return the resulting Markdown string
        return markdown_string


def colored_print(text, color):
    """
    Print colored text in the console.
    
    This function takes a string of text and a color name and prints the text in the specified color
    using ANSI escape codes. The available colors are defined in the color_codes dictionary.
    
    Args:
        text (str): The text to print.
        color (str): The name of the color to use for the text.
    """
    color_codes = {
        'matrix_green': '\033[38;5;77m',
        'amber': '\033[38;5;214m',
        'bright_purple': '\033[38;5;165m',
        'sith_red': '\033[38;5;196m',
        'reset': '\033[0m'
    }
    print(f"{color_codes[color]}{text}{color_codes['reset']}")

def run_oracle_interpreter(queue):
    process = subprocess.Popen(["python", "oracle.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    for line in process.stdout:
        queue.put(line)
    process.stdout.close()
    process.wait()

if __name__ == "__main__":
    # Create an instance of the OracleController
    controller = OracleController()
    
    # Set the Open Interpreter house keeping stack
    open_interpreter_directory = "OpenInterpreter"
    
    
    # Set the allowed workspace directory for general file operations
    allowed_directory = "antikythera"
    
    # Set the storage directory for general long-term storage
    storage_directory = "alexandria"
    
    # Structured data long-term storage
    aetherion_directory = "aetherion"
    
    # Short term memory
    athenium_directory = "athenium"
    
    # Unstructured semiotics long-term storage
    acheron_directory = "acheron"
    
    # Create an instance of the OracleInterpreter with the allowed and storage directories
    oracle_interpreter = OracleInterpreter(allowed_directory, storage_directory, aetherion_directory, athenium_directory, acheron_directory, open_interpreter_directory)
    
    # Create a queue for communication between the main thread and the GUI thread
    queue = queue.Queue()
    
    # After all, why not? Why shouldn't I keep it?
    print(" ")
    print(" ")
    colored_print(" Initializing system... ", "matrix_green")
    print(" ")
    print(" ")
    colored_print("'Welcome to the Oracle Interpreter Interactive Terminal!' ", "amber")
    print(" ")
    colored_print(" [ Brought to you by Mnemosyne Labs, a division of Azoth Corp. ] ", "bright_purple")
    colored_print(" [ www.AzothCorp.com ] ", "bright_purple")
    colored_print(" [ '...Coming soon to a world near you...' ] ", "bright_purple")
    print(" ")
    print(" ")
    colored_print(" Health scan complete. All systems go. ", "matrix_green")
    print(" ")
    colored_print(" Logging you in... ", "matrix_green")
    print(" ")
    print(" ")
    colored_print(" 'Please enter the following command to open the auxiliary GUI:", "amber")
    print(" ") 
    colored_print("    'open aux gui' ", "sith_red")
    print(" ")
    colored_print("  or proceed with the command line interface.' ", "amber")
    print(" ")
    print(" ")
    colored_print(" 'Type 'quit' to exit.' ", "amber")
    print(" ")
    print(" ")
    
    # Start the main loop for user interaction
    while True:
        user_message = input("> ")
        
        if user_message.lower() == 'quit':
            oracle_interpreter.save_conversation_log()
            break
        
        response = oracle_interpreter.parse_command(user_message)
        print(response)
        
        oracle_interpreter.log_interaction(user_message, response)

    oracle_interpreter.save_conversation_log()