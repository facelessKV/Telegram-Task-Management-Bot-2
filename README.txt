✅ Telegram Task Management Bot

Need a bot for efficient task management? This bot will help you organize work, set deadlines, and track task completion!
With this bot, you can manage tasks, assign them to yourself or your team, and receive deadline reminders.

✅ What does it do?

• 📝 Creates, edits, and deletes tasks
• ⏰ Reminds you of upcoming task deadlines
• 👥 Assigns tasks to other users
• 📂 Stores task data in a database

🔧 Functionality

✅ Simple task creation with descriptions and deadlines
✅ Notifications about approaching deadlines
✅ User-friendly interface for all users

📩 Want to increase your team's productivity?

Contact me on Telegram, and I'll help you set up this bot for your business! 🚀

# INSTRUCTIONS FOR INSTALLING AND LAUNCHING A TELEGRAM BOT FOR TASK MANAGEMENT

## FOR WINDOWS USERS

### Step 1: Install Python
1. Open a browser and go to the website https://www.python.org/downloads/
2. Download Python 3.9.13 (not the latest version, as it may have problems installing dependencies)
3. Run the downloaded file (for example, python-3.9.13-amd64.exe )
4. Be sure to check the box "Add Python 3.9 to PATH" before installing!
5. Click "Install Now" and wait for the installation to complete.

### Step 2: Download and prepare the bot
1. Create a folder for the bot on your computer, for example: C:\TelegramTaskBot
2. Copy the bot files (main.py and config.py ) to this folder

### Step 3: Getting a token for the bot
1. Open Telegram and find @BotFather
2. Write a command to the bot /newbot
3. Follow the instructions: enter the name of the bot, and then come up with a unique username that should end with "bot"
4. After creating the bot, you will receive an API token (a long string of letters and numbers), copy it

### Step 4: Setting up the Bot
1. Open the config file.py in any text editor (you can use notepad)
2. Replace 'YOUR_BOT_TOKEN' with the received token (keeping the quotes)
3. Save and close the file

### Step 5: Install the necessary libraries
1. Open the Windows command prompt: press Win+R, type cmd and press Enter
2. Go to the bot folder. For example, type: 
   ```
   cd C:\TelegramTaskBot
   ```
3. Install the necessary libraries using the command:
   ```
   pip install aiogram==3.0.0 apscheduler
   ```
4. Wait for the installation to complete

### Step 6: Launch the Bot
1. At the command prompt, while in the bot folder, type:
   ```
   python main.py
   ```
2. If everything is installed correctly, you will see a message about the launch of the bot.
3. DO NOT CLOSE the command prompt while the bot is running!

### Step 7: Using the Bot
1. Open Telegram and find your bot by the name you specified
2. Press the "Start" button or send the command /start
3. Follow the instructions of the bot to create and manage tasks.

## FOR LINUX USERS

### Step 1: Install Python
1. Open a terminal (Ctrl+Alt+T in most distributions)
2. Update the packages:
   ```
   sudo apt update
   ```
3. Install Python and pip:
``
   sudo apt install python3.9 python3-pip
   ```

### Step 2: Create a folder for the bot
1. Create a folder for the bot:
   ```
   mkdir ~/TelegramTaskBot
   ```
2. Go to this folder:
``
   cd ~/TelegramTaskBot
   ```

### Step 3: Create Bot Files
1. Create a file main.py :
``
   nano main.py
   ```
2. Copy the contents of the file main.py (the entire bot code) in the editor that opens
3. Save the file: press Ctrl+O, then Enter, then Ctrl+X to exit
4. Create a file config.py :
``
   nano config.py
   ```
5. Enter:
   ```python
   BOT_TOKEN = 'YOUR_BOT_TOKEN'  # Here you will need to replace it with your token
   ```
6. Save the file: Ctrl+O, Enter, Ctrl+X

### Step 4: Getting a token for the bot
1. Open Telegram and find @BotFather
2. Write a command to the bot /newbot
3. Follow the instructions: enter the name of the bot, followed by a unique username that must end with "bot"
4. After creating the bot, you will receive an API token (a long string of letters and numbers), copy it

### Step 5: Setting up the bot
1. Open the file config.py for editing purposes:
   ```
   nano config.py
   ```
2. Replace 'YOUR_BOT_TOKEN' with the received token (keeping the quotes)
3. Save the file: Ctrl+O, Enter, Ctrl+X

### Step 6: Install the necessary libraries
1. In the terminal, while in the folder with the bot, enter:
   ```
   pip3 install aiogram==3.0.0 apscheduler
   ```
2. Wait for the installation to complete

### Step 7: Launch the Bot
1. In the terminal, while in the folder with the bot, enter:
   ```
   python3 main.py
   ```
2. If everything is installed correctly, you will see a message about the launch of the bot.
3. DO NOT CLOSE the terminal while the bot is running!

### Step 8: Using the Bot
1. Open Telegram and find your bot by the name you specified
2. Press the "Start" button or send the command /start
3. Follow the instructions of the bot to create and manage tasks.

## BASIC BOT COMMANDS

- /start - Launch the bot and receive a welcome message
- /add_task - Add a new task
- /list_tasks - View the task list
- /update_task - Update an existing task
- /complete_task - Mark the task as completed

## PROBLEM SOLVING

### If the bot does not start:
1. Make sure that you have entered the token correctly in the file config.py
2. Check that all necessary libraries are installed.
3. Check the Python version: type `python --version` or `python3 --version` in the terminal or command prompt

### If the libraries cannot be installed:
1. Try using a different version of Python (3.8 or 3.9)
2. Check your internet connection
3. In Windows, you may need to run the command prompt as an administrator.

### If the bot starts but does not respond in Telegram:
1. Make sure that you are communicating with the correct bot (by username)
2. Make sure that the command prompt or terminal where the bot is running is still running.
3. Check if there are any errors in the console where the bot is running.

## To run the bot in the background (Linux only)

To keep the bot running after the terminal is closed:

1. Install screen:
   ```
   sudo apt install screen
   ```
2. Create a new screen session:
   ```
   screen -S taskbot
   ```
3. Launch the bot as usual:
``
   python3 main.py
   ```
4. Press Ctrl+A, then D to disconnect from the session (the bot will continue to work)
5. To return to the bot later, enter:
   ```
   screen -r taskbot
   ```
