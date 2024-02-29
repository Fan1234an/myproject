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

# 抓前六個標題與連結，並下載圖片
def DiscussionForum1():

    driver.get('https://acg.gamer.com.tw/billboard.php?t=2&p=NS')  

    result = []
    image_paths = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_folder = os.path.join(base_dir, 'static', 'PC')
    
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainbox1'))
        )
        elements = driver.find_elements(By.CLASS_NAME, 'ACG-mainbox1')[:6]  
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ACG-mainbox2B'))
        )
        images = driver.find_elements(By.CLASS_NAME, 'ACG-mainbox2B')[:6]  

        scores, popularities = Score_Popularity_Switch()

        for index, (element, image) in enumerate(zip(elements, images), start=1):
            title = element.find_element(By.TAG_NAME, 'a').text
            href = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
            score = scores[index-1]
            popularity = popularities[index-1]
            img = image.find_element(By.TAG_NAME, 'img')
            src = img.get_attribute('src')
            if not src.startswith('http'):
                src = 'https:' + src

            response = requests.get(src)
            if response.status_code == 200:
                image_name = f'image_{href.split("=")[-1]}.jpg'
                image_path = os.path.join(image_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
                image_paths.append(image_path)
            
            result.append((title, href, image_path, score, popularity)) 
    except Exception as e:
        print(f'出錯: {e}')
    finally:
        driver.quit()  
    return result

def Score_Popularity_Switch():
    
    driver.get('https://acg.gamer.com.tw/billboard.php?t=2&p=NS')  

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

# 儲存資料到資料庫
def save_to_database(data):
    # 建立或打開資料庫
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()

    # 建立資料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY,
        title TEXT,
        url TEXT,
        score TEXT,
        popularity TEXT,
        data BLOB
    )
    ''')

    # 清空现有数据
    cursor.execute('DELETE FROM images')

    # 遍歷數據，將每條數據存儲到資料庫
    for title, url, image_path, score, popularity in data:
        with open(image_path, 'rb') as file:
            image_data = file.read()
            cursor.execute('INSERT INTO images (title, url, score, popularity, data) VALUES (?, ?, ?, ?, ?)', 
                           (title, url, score, popularity, image_data))
    # 提交變更並關閉資料庫連接
    conn.commit()
    conn.close()

def main():
    data = DiscussionForum1()
    save_to_database(data)

if __name__ == "__main__":
    main()
