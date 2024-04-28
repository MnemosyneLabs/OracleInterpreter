```markdown

# Oracle.py

Oracle.py is an easy-to-use modular interpreter system with an auxiliary GUI. Developed by Mnemosyne Labs, a division of Azoth Corp (www.AzothCorp.com), and released as an open source project (subject to LICENSE), Oracle.py provides a powerful and extensible framework for building AI-driven applications, and adding an AI Interpreter module to any project. It also works as a stand alone interpreter system.


## Features

- Current interpreters: Open interpreter 
- Current API support: OpenAI and Anthropic language models
- Auxiliary GUI for instant user interaction and control
- Customizable settings for temperature and max tokens*
- API key management for seamless integration with language model providers
- Code execution within a controlled environment
- Background music and sound effects for an immersive experience
- Workspace and long-term memory directories for file management
- Easy core integration into any project
- Extensively (and hopefully, educationally) commented, to help with setup and use.
- Web browser*

*Broken in GUI


## Installation

To install and set up Oracle.py, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/your-username/oracle.py.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the API keys:
   - Create a `.env` file in the project root directory.
   - Add your OpenAI API key: `OPENAI_API_KEY=your_openai_api_key`
   - Add your Anthropic API key: `ANTHROPIC_API_KEY=your_anthropic_api_key`

4. Set up the Google API Key and Search Engine ID:

   - Obtain a Google API key from the [Google Cloud Console](https://console.cloud.google.com/):
      1. Create or select a Google Cloud project.
      2. Enable the necessary APIs (e.g., Custom Search API).
      3. Under "APIs & Services," go to "Credentials" and create an API key.
      4. Restrict your API key as needed for security.
      5. Copy the API key.

   - Obtain a Google Search Engine ID from [Google Custom Search Engine](https://cse.google.com/):
      1. Create or select a custom search engine.
      2. Note the "Search engine ID" from the setup page.
      3. Configure your custom search engine as needed.
      4. Copy the Search Engine ID.

   - Add the following to your `.env` file:
      ```
      GOOGLE_API_KEY=your_google_api_key
      GOOGLE_SEARCH_ENGINE_ID=your_google_search_engine_id
      ```

5. Run the `oracle.py` script.


## Contents

README.MD
LICENSE - MIT#
requirements.txt
.gitignore
.env - Environment variables (you'll need to create this)

oracle_icon.ico
oracle_background.png
coming soon to a world near you.png
se_1.mp3

oracle.py - Main module file
delphi.py - Auxiliary GUI file
user.py - GUI theme file ("nightcity" by @LericDax)

/oracle_logs - Log files for Oracle Interpreter
/alexandria - Long-term storage for Oracle
/antikythera - File workspace for Oracle
/acheron - Affects and Percepts directory for Oracle
/aetherion - Concepts and Functives directory for Oracle
/athenium - Short-term memory for Oracle
/OpenInterpreter - Open Interpreter directory
/__pycache__ - Python cache files
/fonts - Font files
/Old - Legacy files

/OracleData (Empty)
/OracleDocs (Empty)
/OracleScripts (Empty)
/OracleTests (Empty)



## Usage

1. Launch the Oracle.py application by running `python oracle.py`.
2. Use the command-line interface to interact with the AI.
3. To open the auxiliary GUI, enter the command: `open aux gui`.
4. In the GUI, you can:
   - Adjust the temperature and max tokens settings using the settings panel.*
   - Switch between OpenAI and Anthropic language models using API panel.
   - Manage API keys for the selected provider.
   - Start*, pause*, stop*, and terminate* the Oracle Interpreter.
   - Open the workspace and long-term memory directories.
   - View the conversation history and terminal output.
   - Send commands to the Oracle Interpreter.

*Broken


## Current Limitations and Known Issues

- Some features, such as pausing and resuming the Oracle Interpreter, are not fully functional.
- The GUI may experience performance issues when handling large amounts of data or long-running processes.
- Certain unwanted messages, such as warnings and pygame messages, are filtered out during the initial startup phase.
- The code execution feature is limited to the allowed directory and may not work correctly in all scenarios.
- Whilst it uses protected directories, it should never be left running unattended--extremely experimental technology that can execute files on your system must be closely watched.
- Once you launch the GUI you cannot regain control of the terminal, even by closing the GUI, without crashing the program. You must end the process and restart it.
- The web browser doesn't work. It must be fixed.

## Contributing

We welcome contributions to enhance Oracle.py and address any issues or limitations. We do not promise a functional or complete project, nor accept any liability whatsoever for how it behaves or is used in theory or practice. It is provided as OSS to be used as you wish, in part or whole (according to the requirements of the included LICENSE). To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive commit messages.
4. Push your changes to your forked repository.
5. Submit a pull request detailing your changes and their benefits.

https://github.com/MnemosyneLabs/OracleInterpreter


## License

Oracle.py is released under the [MIT# License](SEE INCLUDED LICENSE).



## Contact

For any questions, suggestions, or feedback, please contact us at opensource@azothcorp.com.


---


Developed by Mnemosyne Labs, a division of Azoth Corp.
"Coming soon to a world near you..."
www.AzothCorp.com
https://github.com/MnemosyneLabs
Original project author and initalization by: 
Logan Kirkland (www.LericDax.com)
https://github.com/LericDax
```