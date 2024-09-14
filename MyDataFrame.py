import time
import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

# Настройка логирования
logging.basicConfig(filename='data_collection.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chrome_options = Options()
chrome_options.add_argument('--headless')  # Запуск в фоновом режиме без GUI
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Запуск браузера с прокси
try:
    driver = webdriver.Chrome(options=chrome_options)
    logging.info("WebDriver initialized successfully")
except Exception as e:
    logging.error(f"Error initializing WebDriver: {e}")
    exit(1)

# Открытие сайта
try:
    driver.get("https://gwnw47x.life/games/crash")
    logging.info("Website opened successfully")
except Exception as e:
    logging.error(f"Error opening URL: {e}")
    driver.quit()
    exit(1)

# Функция для получения коэффициента с помощью BeautifulSoup
def get_coefficient_bs4(driver):
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        coefficient_element = soup.select_one("div.ratio-timer__white span")
        coefficient = coefficient_element.text if coefficient_element else None
        return coefficient
    except Exception as e:
        logging.error(f"Error while parsing data with BS4: {e}")
        return None

# Функция для получения данных с помощью Selenium
def get_game_data(driver):
    try:
        coefficient_element = driver.find_element(By.CSS_SELECTOR, "div.ratio-timer span")
        coefficient = coefficient_element.text
    except:
        coefficient = get_coefficient_bs4(driver)

    try:
        total_bets_element = driver.find_element(By.CSS_SELECTOR, "div.head-list__crash span")
        total_bets = total_bets_element.text
    except Exception as e:
        logging.error(f"Error while scraping TotalBets with Selenium: {e}")
        total_bets = None

    return coefficient, total_bets

# Создание CSV файла и запись заголовков
with open('data.csv', mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['GameNumber', 'Coefficient', 'TotalBets', 'EndTime', 'DayOfWeek'])
    writer.writeheader()

    game_number = 1
    last_stable_coefficient_time = time.time()
    last_coefficient = None
    last_total_bets = None
    consecutive_failures = 0

    while True:
        current_time = time.time()
        coefficient, total_bets = get_game_data(driver)

        if coefficient and coefficient.strip() != '':
            last_coefficient = coefficient
            last_total_bets = total_bets
            consecutive_failures = 0
        else:
            consecutive_failures += 1

            if consecutive_failures >= 1:
                if last_coefficient is not None and last_coefficient.strip() != '':
                    stable_time_threshold = 0.05

                    if current_time - last_stable_coefficient_time >= stable_time_threshold:
                        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        end_day_of_week = datetime.now().strftime('%A')

                        game_data = {
                            'GameNumber': game_number,
                            'Coefficient': last_coefficient,
                            'TotalBets': last_total_bets,
                            'EndTime': end_time,
                            'DayOfWeek': end_day_of_week
                        }

                        writer.writerow(game_data)
                        file.flush()
                        logging.info(f"Game {game_number} (failure mode): {game_data}")
                        game_number += 1

                        last_coefficient = None
                        last_stable_coefficient_time = current_time
                        consecutive_failures = 0

driver.quit()
