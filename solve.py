import time, requests, random, string, json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import speech_recognition as sr
import subprocess
class Log:
    def success(text):
        return print(f"[+]: {text}")
    def normal(text):
        return print(f"[=]: {text}")
    def error(text):
        return print(f"[-]: {text}")
    def warn(text):
        return print(f"[\]: {text}")
class Recaptcha:
    def __init__(self) -> None:
        self.captchas_solved = 0
        self.errors = 0
        with open('config.json') as f:
            data = f.read()
            data = json.loads(data)
            self.headless = data['headless']
            self.only_display_token = data['Only_display_token']
            del data
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        self.driver = uc.Chrome(options=options)
    def download_audio(self, url, file_name):
        bytes = requests.get(url).content
        with open(f"audio/{file_name}.mp3", "wb") as f:
            f.write(bytes)
        time.sleep(2)
        self.convert_mp3_to_wav(file_name)
        audio_text = self.speech_recognition(file_name)
        return audio_text
    def speech_recognition(self, file_name):
        r = sr.Recognizer()
        with sr.AudioFile(f"audio/{file_name}.wav") as source:
            audio = r.record(source)
        try:
            s = r.recognize_google(audio)
            return s
        except Exception as e:
            self.driver.quit()
            Log.error("Error Decoding Recaptcha Audio Challenge!")
            return 
    def convert_mp3_to_wav(self, file_name=None):
        try:
            subprocess.call(['ffmpeg', '-i', f"audio/{file_name}.mp3", f"audio/{file_name}.wav"], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as err:
            self.driver.quit()
            Log.error("You need to install ffmpeg on this device in order to convert mp3 files to .wav files!")
            return 
        return
    def solve(self):
        try:
            self.driver.get('https://www.google.com/recaptcha/api2/demo')
            self.driver.switch_to.frame(0)
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div[1]/div/div/span/div[1]'))).click()
            if self.only_display_token == False:
                Log.normal("Fetched Recaptcha")
            self.driver.switch_to.default_content()
        except Exception:
            self.driver.quit()
            Log.error("Error Getting Recaptcha!")
            return 
        try:
            self.driver.switch_to.frame(self.driver.find_elements(By.XPATH, "/html/body/div[2]/div[4]/iframe")[0])
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[3]/div[2]/div[1]/div[1]/div[2]/button'))).click()
            download_link = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[7]/a'))).get_attribute('href')
            if self.only_display_token == False:
                Log.normal(f"Retrived Recaptcha Audio Challenge ({download_link})")
        except Exception:
            self.driver.quit()
            Log.error("Recaptcha seems to be ratelimited on this IP!")
            return
        try:
            audio_text = self.download_audio(download_link, f"recaptcha{random.randint(1, 500000)}{download_link[len(download_link)-15]}")
            if self.only_display_token == False:
                Log.normal(f"Solved Recaptcha Audio Challenge --> ({audio_text})")
            audio_input = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/div/div[6]/input'))).send_keys(audio_text)
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[8]/div[2]/div[1]/div[2]/button'))).click()
            self.driver.switch_to.default_content()
            try:
                self.driver.switch_to.frame(self.driver.find_elements(By.XPATH, "/html/body/div[1]/form/fieldset/ul/li[5]/div/div/div/div/iframe")[0])
            except Exception:
                pass
            captcha_response = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/input'))).get_attribute('value')
            Log.success(f"Solved Recaptcha --> ({captcha_response})")
        except Exception as err:
            input(err)
            Log.error("Error Sumbitting Recaptcha Answer!")
            return
        self.driver.quit()
        return captcha_response
if __name__ == "__main__":
    Recaptcha = Recaptcha()