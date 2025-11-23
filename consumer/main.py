import pika
import json
import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "avito_scraping_queue")
SELENIUM_HUB_URL = os.getenv("SELENIUM_HUB_URL", "http://selenium-hub:4444/wd/hub")

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)


def get_selenium_driver():
    logger.info(f"Создание WebDriver, подключение к {SELENIUM_HUB_URL}")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        logger.info("Инициализация Remote WebDriver...")
        driver = webdriver.Remote(
            command_executor=SELENIUM_HUB_URL,
            options=chrome_options,
            keep_alive=True
        )
        logger.info("Selenium WebDriver успешно создан")
        return driver
    except Exception as e:
        logger.error(f"Ошибка при создании WebDriver: {e}", exc_info=True)
        raise


def scrape_avito_page(url: str):
    driver = None
    try:
        logger.info(f"Начинаю парсинг страницы: {url}")
        driver = get_selenium_driver()
        
        driver.get(url)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
        except TimeoutException:
            logger.warning("Таймаут при ожидании загрузки страницы")
        
        html = driver.page_source
        
        logger.info(f"HTML страницы получен, размер: {len(html)} символов")
        logger.info("=" * 80)
        logger.info("HTML СОДЕРЖИМОЕ СТРАНИЦЫ:")
        logger.info("=" * 80)
        logger.info(html)
        logger.info("=" * 80)
        logger.info(f"Конец HTML содержимого для URL: {url}")
        
        return html
        
    except WebDriverException as e:
        logger.error(f"Ошибка Selenium при парсинге {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при парсинге {url}: {e}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии WebDriver: {e}")


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body)
        url = message.get("url")
        
        if not url:
            logger.error("URL не найден в сообщении")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        logger.info(f"Получена задача на парсинг: {url}")
        
        scrape_avito_page(url)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Задача успешно обработана: {url}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    logger.info("Запуск consumer сервиса...")
    logger.info(f"Подключение к RabbitMQ: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    logger.info(f"Очередь: {RABBITMQ_QUEUE}")
    logger.info(f"Selenium Hub: {SELENIUM_HUB_URL}")
    
    while True:
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            
            channel.basic_qos(prefetch_count=1)
            
            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=process_message
            )
            
            logger.info("Ожидание сообщений из очереди. Для выхода нажмите CTRL+C")
            channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания, завершение работы...")
            if 'channel' in locals():
                channel.stop_consuming()
            if 'connection' in locals() and not connection.is_closed:
                connection.close()
            break
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            logger.info("Повторная попытка подключения через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    main()
