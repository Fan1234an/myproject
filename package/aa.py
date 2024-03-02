import requests
import psycopg2
import urllib.parse as urlparse
import os
from bs4 import BeautifulSoup
import urllib.request as req

# 抓取標題.連結.圖片二進制.評分.人氣
def scrape_and_download_images(base_url, headers):
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    elements = soup.select('div.ACG-mainbox2 h1 a:not(:nth-of-type(2))')[:6]
    image_elements = soup.select('div.ACG-mainbox2B a img')[:6]
    scores, popularity = Score_Popularity_Switch()
    data = []
    for idx, (element, image_element) in enumerate(zip(elements, image_elements)):
        title = element.text.strip()
        link = element['href']
        image_url = image_element['src']
        if not image_url.startswith('http'):
            image_url = 'https:' + image_url

        # 使用requests下载图片并获取二进制内容
        image_response = requests.get(image_url)
        image_content = image_response.content

        # 使用索引获取对应的评分和人气值
        score = scores[idx] if idx < len(scores) else 'N/A'
        pop = popularity[idx] if idx < len(popularity) else 'N/A'

        # 将数据添加到列表中
        data.append((title, link, image_content, score, pop))
    return data

def Score_Popularity_Switch():
    url = 'https://acg.gamer.com.tw/billboard.php?t=2&p=NS'
    request = req.Request(url, headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
    
    Scores = []
    Popularity =[]
    try:
        with req.urlopen(request) as response:
            data = response.read().decode("utf-8")
            root = BeautifulSoup(data, "html.parser")
            elements = root.select('p.ACG-mainplay')[:6]
            for element in elements:
                    pop = element.text.strip()
                    Popularity.append((pop)) #人氣

            elements = root.select('p.ACG-mainboxpoint')[:6]
            for element in elements:
                    score = element.text.strip()
                    Scores.append((score)) #評分
            return Scores,Popularity
    except Exception as e:
        print(f'Error occurred: {e}')

# 儲存資料到資料庫
def save_to_database(data):
    DATABASE_URL = os.environ.get('DATABASE_URL')
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    cursor = conn.cursor()
    # 清空现有数据
    cursor.execute('DELETE FROM images')

    # 遍歷數據，將每條數據存儲到資料庫
    for title, url, image_content, score, pop in data:
        insert_query = """
        INSERT INTO images (title, url, score, popularity, data) VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (title, url, score, pop, image_content))
    # 提交變更並關閉資料庫連接
    conn.commit()
    cursor.close()
    conn.close()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
BASE_URL = 'https://acg.gamer.com.tw/billboard.php?t=2&p=NS'

def main():
    data = scrape_and_download_images(BASE_URL, HEADERS)
    save_to_database(data)

if __name__ == "__main__":
    main()
