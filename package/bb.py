import sqlite3
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from selenium.webdriver.chrome.service import Service
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless") #無頭模式
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")


service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
driver = webdriver.Chrome(service=service, options=chrome_options)

def DiscussionForumACG():
    
    driver.get('https://acg.gamer.com.tw/billboard.php?t=2&p=anime')

    result = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_folder = os.path.join(base_dir, 'static', 'ACG')

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainbox1'))
        )
        titles_and_urls = [
            (
                element.find_element(By.TAG_NAME, 'a').text,
                element.find_element(By.TAG_NAME, 'a').get_attribute('href')
            )
            for element in driver.find_elements(By.CLASS_NAME, 'ACG-mainbox1')[:6]
        ]

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainbox2B'))
        )
        images = [
            element.find_element(By.TAG_NAME, 'img').get_attribute('src')
            for element in driver.find_elements(By.CLASS_NAME, 'ACG-mainbox2B')[:6]
        ]

        scores, popularities = Score_Popularity_ACG()

        for index, (title_url, image_src) in enumerate(zip(titles_and_urls, images), start=1):
            title, url = title_url
            score = scores[index - 1]
            popularity = popularities[index - 1]
            
            if not image_src.startswith('http'):
                image_src = 'https:' + image_src

            response = requests.get(image_src)
            if response.status_code == 200:
                image_data = response.content
                result.append((title, url, score, popularity, image_data))
            else:
                result.append((title, url, score, popularity, None))
    except Exception as e:
        print(f'Error occurred: {e}')
    finally:
        driver.quit()

    return result

def handle_image_download(image_src, image_folder, index):
    if not image_src.startswith('http'):
        image_src = 'https:' + image_src

    response = requests.get(image_src)
    image_name = f'image_{index}.jpg'
    image_path = os.path.join(image_folder, image_name)
    
    if response.status_code == 200:
        with open(image_path, 'wb') as file:
            file.write(response.content)

    return image_path

def Score_Popularity_ACG():
    
    driver.get('https://acg.gamer.com.tw/billboard.php?t=2&p=anime')  

    Scores = [] 
    popularity = [] 
    try:
        #先抓評分
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainbox4'))
        )
        elements = driver.find_elements(By.CLASS_NAME, 'ACG-mainbox4') 
        for element in elements[:6]:  
            all = element.find_element(By.TAG_NAME, 'p') 
            text = all.text
            Scores.append(text.replace('\n', ''))  
        
        #再抓人氣
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainplay'))
        )
        elements = driver.find_elements(By.CLASS_NAME, 'ACG-mainplay')    
        for element in elements[:6]:  
            text = element.text
            popularity.append(text.replace('\n', ''))  
    except Exception as e:
        print(f'出錯: {e}')
    finally:
        driver.quit()  
    return Scores,popularity

def save_to_database(data):
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS acg_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        score TEXT,
        popularity TEXT,
        image BLOB
    )
    ''')

    cursor.execute('DELETE FROM acg_info')

    for title, url, score, popularity, image_data in data:
        # 將圖片二進位數據插入到數據庫
        cursor.execute('''
        INSERT INTO acg_info (title, url, score, popularity, image) 
        VALUES (?, ?, ?, ?, ?)
        ''', (title, url, score, popularity, image_data))

    conn.commit()
    conn.close()

def maina():
    data = DiscussionForumACG()
    save_to_database(data)

if __name__ == "__main__":
    maina()
