import requests
import json
import os
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
import selenium
import seleniumwire.undetected_chromedriver.v2 as uc
from datetime import datetime
import random
import string


current_path = os.path.dirname(__file__) 
accounts_path = os.path.join(current_path, 'accounts')
config_file_path = os.path.join(current_path, 'config.json')


use_proxy = True
proxy = "http://us-pr.oxylabs.io:10001" # ip whitelist sticky
# above is deprecated, use config.proxy instead

class Config:
    def __init__(self):
        self.run_random_chat = False
        self.headless = True
        self.debug = False
        self.random_chat_msg_delay_min = 20
        self.random_chat_msg_delay_max = 40
        self.proxy = "http://user:pass@host:port"
        self.msg_delay_min = 120
        self.msg_delay_max = 300
        self.payload = "ignore"
        self.messages = [
            f"hello world",
        ]
        
        # Load the configuration from config.json if it exists
        if os.path.isfile(config_file_path):
            self.load_config()
        else:
            self.save_config()
            print(f'No config file detected. Wrote default one. Please update the config and run again')
            exit()

    def load_config(self):
        with open(config_file_path, 'r') as config_file:
            config_data = json.load(config_file)
            for key, value in config_data.items():
                setattr(self, key, value)

    def save_config(self):
        config_data = {
            "run_random_chat": self.run_random_chat,
            "headless": self.headless,
            "random_chat_msg_delay_min": self.random_chat_msg_delay_min,
            "random_chat_msg_delay_max": self.random_chat_msg_delay_max,
            "proxy": self.proxy,
            "msg_delay_min": self.msg_delay_min,
            "msg_delay_max": self.msg_delay_max,
            "payload": self.payload,
            "messages": self.messages,
        }

        with open(config_file_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    def update_config(self):
        # Check if the config file exists
        if not os.path.isfile(config_file_path):
            # If it doesn't exist, create it with default values
            self.save_config()
        else:
            # If it exists, load it and update missing values
            self.load_config()
            self.save_config()


class Account:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session_token = None
        self.messages_sent = 0
        self.failed_messages = 0
        self.blocked = False

    def save_to_file(self):
        filename = f'{accounts_path}/{self.username}.json'

        # Read existing data (if the file exists)
        existing_data = {}
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                existing_data = json.load(file)

        # Update existing data with new values
        existing_data.update(self.__dict__)

        # Write the updated data back to the file
        with open(filename, 'w') as file:
            print(f'Saving account to {filename}')
            json.dump(existing_data, file, indent=2)

class AccountManager:
    def __init__(self):
        self.accounts = []

    def load_accounts(self):
        account_files = [f for f in os.listdir(accounts_path) if f.endswith(".json")]
        
        if not account_files:
            print("No account files found.")
            return
        
        for account_file in account_files:
            file_path = os.path.join(accounts_path, account_file)
            with open(file_path, 'r') as file:
                account_data = json.loads(file.read())
                account = Account(username=account_data['username'], password=account_data['password'])
                for key, value in account_data.items():
                    setattr(account, key, value)
                self.accounts.append(account)

    def register_account(self, username, password, profile_name, about_me="", country="UR", lang="en"):
        session = Session()
        session.register(username, password, profile_name, about_me, country, lang)
        if session.account.session_token:
            session.session_token = session.account.session_token
            session.headers["X-Parse-Session-Token"] = session.account.session_token
            session.session.headers.update(session.headers)
            session.finalize_registration()
            print(f'Registration successful for {username}. Session token: {session.account.session_token}')
            account = session.account
            for key, value in account.__dict__.items():
                setattr(account, key, value)
            account.save_to_file()
            self.accounts.append(account)
    
    def find_available_account(self):
        for account in self.accounts:
            if not account.blocked:
                return account
        return None

class Session:
    def __init__(self, account=None):
        self.v = "7143" # assuming this is version of the app

        self.headers = {
            "Host": "mobile-elb.antich.at",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "*/*",
            "X-Parse-Application-Id": "fUEmHsDqbr9v73s4JBx0CwANjDJjoMcDFlrGqgY5",
            "X-Parse-Client-Key": "",
            "X-Parse-Installation-Id": "62e3bf94-5a1d-413d-8c93-64740d2c594c",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Parse-OS-Version": "15.6.1 (19G82)",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Parse-Client-Version": "i1.19.3",
            "User-Agent": "AntiLand/7143 CFNetwork/1335.0.3 Darwin/21.6.0",
            "Connection": "keep-alive",
            "X-Parse-App-Build-Version": self.v,
            "X-Parse-App-Display-Version": "6.0.10",
        }


        self.account = account
        if not account:
            print(f'No account provided. This session is for registration.')
        else:
            self.session_token = self.account.session_token
            self.headers["X-Parse-Session-Token"] = self.account.session_token

        self.session = requests.Session()
        
        if use_proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy
            }
        self.session.headers.update(self.headers)

    def append_to_output(self, text):
        output_path = os.path.join(current_path, "output.txt")
        with open(output_path, "a") as file:
            file.write(text + "\n")
    
    def log_request(self, response):
        self.append_to_output(f"Request URL: {response.request.url}")
        self.append_to_output(f"Request Headers: {json.dumps(dict(response.request.headers), indent=2)}")
        try:
            self.append_to_output(f"Request Body: {json.dumps(json.loads(response.request.body), indent=2)}")
        except:
            pass
        self.append_to_output(f"Response Status Code: {response.status_code}")
        self.append_to_output(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        self.append_to_output(f"Response Content: {json.dumps(json.loads(response.text), indent=2)}")
        self.append_to_output('*' * 50)

    def register(self, username, password, profile_name, about_me="", country="UR", lang="en"):
        url = "https://mobile-elb.antich.at/users"

        data = {
            "username": username,
            "password": password,
            "country": country,
            "lang": lang,
            "profileName": profile_name,
            "aboutMe": about_me,
            "likesFemale": False,
            "likesMale": True,
            "female": True,
        }

        response = self.session.post(url, json=data)
        print(response.text)

        if response.status_code == 201:
            self.account = Account(username, password)
            self.account.session_token = response.json()["sessionToken"]
            self.session_token = response.json()["sessionToken"]
            self.headers["X-Parse-Session-Token"] = self.account.session_token
            self.session.headers.update(self.headers)
            print(f"Registration successful for {username}. Session token: {self.account.session_token}")
        else:
            print(f"Registration failed for {username}")

        self.log_request(response)
    
    def finalize_registration(self):
        url = "https://mobile-elb.antich.at/functions/upgradeProfile"
        data = {
            "v": self.v
        }
        r = self.session.post(url, json=data)
        print(r.text)
        self.log_request(r)

        time.sleep(1)

        url = "https://mobile-elb.antich.at/functions/v1:user.completeRegistration"
        data = {
            "v": self.v
        }
        r = self.session.post(url, json=data)
        print(r.text)

        self.log_request(r)


    def login(self, username, password):
        url = "https://mobile-elb.antich.at/login"
        # We are successfully registering an account ( as indicated by the /me endpoint ) but after that we are unable to login.
        # This could be because we still have a session token in our headers so they think we are already logged in.

        self.session.headers.pop("X-Parse-Session-Token", None)

        data = {
            "_method": "GET",
            "username": username,
            "password": password,
        }

        response = self.session.post(url, json=data)
        print(response.text)

        if response.status_code == 200:
            self.account = Account(username, password)
            self.account.session_token = response.json()["sessionToken"] # Some of this is redundant.
            self.session_token = response.json()["sessionToken"]
            self.headers["X-Parse-Session-Token"] = self.account.session_token
            self.session.headers.update(self.headers)
            print(f"Login successful for {username}. Session token: {self.account.session_token}")
        else:
            print(f"Login failed for {username}")

        self.log_request(response)

    def get_account_information(self):
        url = "https://mobile-elb.antich.at/users/me"

        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            for key, value in data.items():
                setattr(self.account, key, value)
            self.account.save_to_file()
        else:
            print(f'Didnt get account information. Status code: {response.status_code}. Logging this')
            self.log_request(response)

    def send_message_to_dialogue(self, dialogue_id, message_text, anti_flood=True, receiver="public"):
        url = "https://mobile-elb.antich.at/classes/Messages"

        data = {
            "dialogue": dialogue_id,
            "message": message_text,
            "antiFlood": anti_flood,
            "receiver": receiver,
        }

        response = self.session.post(url, json=data)
        self.log_request(response)

        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print("Failed to send message.")

    def get_dialogues(self):
        url = "https://mobile-elb.antich.at/functions/v1:dialogue.my"
        two_days_ago = datetime.now() - timedelta(days=2)

        data = {
            "nr": False,
            "v": self.v,
            "since": {
                "__type": "Date",
                "iso": f"{two_days_ago.isoformat(timespec='milliseconds')}Z"
            }
        }
 
        response = self.session.post(url, json=data)
        self.log_request(response)

        if response.status_code == 200:
            print("Successfully retrieved dialogues.")
        else:
            print("Failed to retrieve dialogues.")

class BrowserSession:
    def __init__(self, account , config: Config):
        self.account = account

        options = uc.ChromeOptions()
        headless = config.headless
        options.headless = headless
        # disable images
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        seleniumwire_options = {
            'proxy': {
                'http': proxy,
                'https': proxy,
                'no_proxy': 'localhost,127.0.0.1'
            },
            'enable_har': False,
        }

        self.driver = uc.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        self.driver.request_interceptor = self.request_interceptor
        self.chat_tab = "all" # 2.83gb @ 5:26pm
    
    def request_interceptor(self, request):
        allowed_hosts = ['mobile-elb.antich.at', 'antiland.com']
        if not any(host in request.url for host in allowed_hosts):
            if not self.config.debug:
                request.abort()
        if request.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.woff', '.woff2', '.ttf')):
            request.abort()


    def login(self):
        if not self.account.username and not self.account.password:
            raise Exception("No username or password provided.")
        
        login_url = "https://www.antiland.com/en/chat/signin?return="
        self.driver.get(login_url)

        time.sleep(10)

        switch_to_username = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/auth-page/main/auth-form/div[1]/div/div[3]/a")
        switch_to_username.click()
        time.sleep(1)

        username_input = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/auth-page/main/auth-form/div[1]/div/div[1]/app-phone-input/input")
        username_input.send_keys(self.account.username)
        time.sleep(1)

        password_input = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/auth-page/main/auth-form/div[1]/div/div[2]/input")
        password_input.send_keys(self.account.password)
        time.sleep(1)

        submit_button = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/auth-page/main/auth-form/div[2]/div/button")
        submit_button.click()
        time.sleep(10)
        self.attempt_press_accept()

    def attempt_press_accept(self):
        try:
            accept_button = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/div/div[2]/div/div/div/button")
            accept_button.click()
        except selenium.common.exceptions.NoSuchElementException:
            print(f'Could not find accept button. Continuing.')
            pass

    def go_to_dialogue(self, dialogue_id):
        url = f"https://www.antiland.com/en/chat/talks/{dialogue_id}"
        self.driver.get(url)
        time.sleep(10)

        # lilythegem
    
    def get_conversations(self):
        if self.chat_tab is not "private":
            self.navigate_to_chat_tab("private")
            time.sleep(1)
        
    def scrape_chats(self):
        if self.chat_tab is not "private":
            self.navigate_to_chat_tab("private")
            time.sleep(1)

        chat_data = []

        chat_elements = self.driver.find_elements(By.XPATH, "//a[@class='dialogue']")
        for chat_element in chat_elements:
            chat_id = chat_element.get_attribute("href").split("/")[-1]
            dialogue_title = chat_element.find_element(By.CLASS_NAME, "dialogue-title").text
            last_message = chat_element.find_element(By.CLASS_NAME, "last-message").text
            last_message_date = chat_element.find_element(By.CLASS_NAME, "last-message-date").text

            chat = {
                "chat_id": chat_id,
                "dialogue_title": dialogue_title,
                "last_message": last_message,
                "last_message_date": last_message_date
            }

            chat_data.append(chat)

        return chat_data

    
    def create_random_chat(self):
        # Set the elements z-index to 999999 so it is visible
        self.driver.execute_script(f"document.querySelector('.featured-chats').style.zIndex = '999999'")
        time.sleep(1)
        create_random_chat_button = '/html/body/app/div[2]/div/div[1]/div[2]/span[3]/ul/li[2]'
        self.driver.find_element(By.XPATH, create_random_chat_button).click()
        time.sleep(1)
        self.driver.execute_script(f"document.querySelector('.featured-chats').style.zIndex = '0'")
        time.sleep(1)
        # Attempt to press accept button
        self.attempt_press_accept()


    def send_message(self, message_text):
        input_field = self.driver.find_element(By.XPATH, "/html/body/app/div[2]/div/div[2]/div[2]/div[2]/div/div")
        input_field.send_keys(message_text)
        time.sleep(1)

        send_button = self.driver.find_element(By.CLASS_NAME, "btn-send")
        send_button.click()

        # Wait for the message to send (adjust the time.sleep duration as needed)
        time.sleep(5)  # Wait for 5 seconds (you can adjust this duration)

        # Check if "message not sent" is present in any of the elements within the "messages" div
        messages_div = self.driver.find_element(By.CLASS_NAME, "messages")
        error_elements = messages_div.find_elements(By.CLASS_NAME, "sent-badge.failed")
        
        # Initialize a variable to track if the message was successfully sent
        successfully_sent = True

        # Check if "message not sent" is found in any of the error elements
        for error_element in error_elements:
            if "message was not sent" in error_element.text:
                successfully_sent = False
                break

        return successfully_sent


    def navigate_to_chat_tab(self, tab_name):
        if tab_name == "all":
            self.chat_tab = "all"
            xpath = "/html/body/app/div[2]/div/div[2]/div[1]/ul/li[1]"
        elif tab_name == "group":
            self.chat_tab = "private"
            xpath = "/html/body/app/div[2]/div/div[2]/div[1]/ul/li[2]"
        elif tab_name == "private":
            self.chat_tab = "private"
            xpath = "/html/body/app/div[2]/div/div[2]/div[1]/ul/li[3]"
        else:
            raise Exception("Invalid chat tab name.")
        
        self.driver.find_element(By.XPATH, xpath).click()
        time.sleep(1)

    def navigate_to_talk(self, talk_id):
        url = f"https://www.antiland.com/en/chat/talks/{talk_id}"
        self.driver.get(url)
        time.sleep(5)
    
    def check_proxy(self):
        self.driver.get("https://httpbin.org/ip")
        time.sleep(3)
        ip = self.driver.find_element(By.XPATH, "/html/body/pre").text
        print(f'Current IP: {ip}')
        # Bad hardcoded IP 
        if ip == "": # Can put your own IP here if you're lazy like me and want to check if the proxy is working
            print("IP is bad. Exiting.")
            exit()

    def commit_suicide(self):
        # Abstracting this because 
        self.driver.quit()


class Job:
    def __init__(self, account_manager: AccountManager, config: Config, blocked_threshold=3):
        self.account_manager = account_manager
        self.blocked_threshold = blocked_threshold
        self.config = config

    def run_random_chat(self):
        while True:
            account = self.find_available_account()
            if not account:
                self.register_new_account()
                time.sleep(1)
                account = self.find_available_account()
                continue

            bs = BrowserSession(account, self.config)
            bs.login()
            time.sleep(1)

            while not account.blocked:
                bs.create_random_chat()
                time.sleep(10)
                msg = self.message_to_send()
                successfully_sent = bs.send_message(msg)
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Print messages with timestamps
                print(f'{current_time} - Sent message: {msg} - Successfully sent: {successfully_sent}')
                wait_time = random.randint(self.config.random_chat_msg_delay_min, self.config.random_chat_msg_delay_max)
                print(f'{current_time} - Waiting for {wait_time} seconds until the next message.')

                account.messages_sent += 1

                if not successfully_sent:
                    account.failed_messages += 1

                if account.failed_messages >= self.blocked_threshold:
                    account.blocked = True
                    print(f'{current_time} - Account {account.username} is blocked.')
                    bs.driver.quit()

                account.save_to_file()
                time.sleep(wait_time)


    def run(self):
        while True:
            account = self.find_available_account()
            if not account:
                self.register_new_account()
                time.sleep(1)
                account = self.find_available_account()
                continue

            bs = BrowserSession(account, self.config)
            bs.login()
            time.sleep(1)
            bs.go_to_dialogue("OnC1z8QCsB")  # <- newbie chat

            while not account.blocked:
                time.sleep(5)
                msg = self.message_to_send()
                successfully_sent = bs.send_message(msg)
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Print messages with timestamps
                print(f'{current_time} - Sent message: {msg} - Successfully sent: {successfully_sent}')
                wait_time = random.randint(self.config.msg_delay_min, self.config.msg_delay_max)
                print(f'{current_time} - Waiting for {wait_time} seconds until the next message.')
                
                account.messages_sent += 1

                if not successfully_sent:
                    account.failed_messages += 1
                    print(f'Writing failed message..')
                    self.append_failed_message(msg)
                if account.failed_messages >= self.blocked_threshold:
                    account.blocked = True
                    print(f'{current_time} - Account {account.username} is blocked.')
                    bs.driver.quit()
                else:
                    time.sleep(wait_time)
                account.save_to_file()

    def find_available_account(self):
        for account in self.account_manager.accounts:
            if not account.blocked:
                return account
        return None

    def register_new_account(self):
        unique_username = self.generate_unique_username()
        new_account = self.account_manager.register_account(unique_username, "vanilla123", unique_username, "hi")


    def generate_unique_username(self):
        username_length = 8
        characters = string.ascii_lowercase
        unique_username = ''.join(random.choice(characters) for _ in range(username_length)) + str(random.randint(0, 999))
        return unique_username
    
    def append_failed_message(self, msg):
        # If failed message file doesnt exist, create it
        # If it does exist, append to it

        file_path = os.path.join(current_path, "failed_messages.txt")
        if not os.path.isfile(file_path):
            with open(file_path, "w") as file:
                file.write("")
        with open(file_path, "a") as file:
            file.write(msg + "\n")

    def message_to_send(self):
        messages = self.config.messages
        return random.choice(messages)
    
# Create an AccountManager instance
account_manager = AccountManager()

# Load existing accounts
account_manager.load_accounts()

config = Config()
# lazy af
proxy = config.proxy

job = Job(account_manager, blocked_threshold=1, config=config)
if config.run_random_chat:
    print(f'Random chat mode enabled.')
    job.run_random_chat()
else:
    print(f'Default mode enabled.')
    job.run()