from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import pika
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Avito Property Scraper API", version="1.0.0")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "avito_scraping_queue")


class BrowseRequest(BaseModel):
    url: HttpUrl

class BrowseResponse(BaseModel):
    message: str
    url: str

def get_rabbitmq_connection():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        logger.error(f"Ошибка подключения к RabbitMQ: {e}")
        raise


def publish_to_queue(url: str):
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        message = json.dumps({"url": str(url)})
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ),
        )
        
        logger.info(f"Задача добавлена в очередь: {url}")
        channel.close()
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка при публикации в очередь: {e}")
        raise


@app.get("/health")
async def health_check():
    try:
        connection = get_rabbitmq_connection()
        connection.close()
        return {"status": "healthy", "service": "api"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "api", "error": str(e)}


@app.post("/browse", response_model=BrowseResponse)
async def browse(request: BrowseRequest):
    try:
        url_str = str(request.url)
        logger.info(f"Получен запрос на парсинг: {url_str}")
        
        if "avito.ru" not in url_str.lower():
            raise HTTPException(
                status_code=400,
                detail="URL должен быть с сайта avito.ru"
            )
        
        publish_to_queue(url_str)
        
        return BrowseResponse(
            message="Задача успешно добавлена в очередь",
            url=url_str
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.get("/")
async def root():
    return {
        "service": "Avito Property Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "POST /browse": "Add URL for parsing",
            "GET /health": "Check health of the service"
        }
    }
