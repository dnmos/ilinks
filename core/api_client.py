# core/api_client.py

import requests
import logging
import time
from typing import List, Dict, Tuple, Optional
from core.utils import get_logger

logger = get_logger(__name__)

def get_all_posts(base_url: str, per_page: int = 100) -> List[Dict[str, any]]:
    """
    Получает список всех статей с их ID и slug из WordPress REST API.

    Args:
        base_url (str): Базовый URL сайта WordPress.
        per_page (int): Количество статей на странице (максимум 100).

    Returns:
        list: Список словарей, где каждый словарь содержит 'id' и 'slug' статьи.
              Возвращает пустой список в случае ошибки.
    """
    all_posts: List[Dict[str, any]] = []
    page: int = 1
    total_pages: Optional[int] = None

    try:
        # 1. Get the first page and extract total number of pages
        api_url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}&page={page}"
        logger.info(f"Запрос к API: {api_url}")
        response = _make_request(api_url)
        if response is None:
            return []

        total_pages = int(response.headers.get('X-WP-TotalPages')) if response.headers.get('X-WP-TotalPages') else 1  # Get total pages from headers
        posts: List[Dict[str, any]] = response.json()

        if not posts:
            logger.warning("No posts found on the first page.")
            return []

        for post in posts:
            all_posts.append({"id": post["id"], "slug": post["slug"]})

        # 2. Loop through the remaining pages (if any)
        page = 2  # Start from the second page
        while page <= (total_pages or 1):
            api_url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}&page={page}"
            logger.info(f"Запрос к API: {api_url}")
            response = _make_request(api_url)
            if response is None:
                break

            posts = response.json()
            if not posts:
                logger.warning(f"No posts found on page {page}.")
                break

            for post in posts:
                all_posts.append({"id": post["id"], "slug": post["slug"]})

            page += 1

    except Exception as e: # Более общий обработчик для непредвиденных ошибок
        logger.error(f"Непредвиденная ошибка при получении списка статей (страница {page}): {e}", exc_info=True)
        return []  # Return an empty list in case of error

    return all_posts


def get_post_content(base_url: str, post_id: int) -> Tuple[str, Dict[str, any]]:
    """
    Получает контент статьи и данные из поля acf по ее ID из WordPress REST API.

    Args:
        base_url (str): Базовый URL сайта WordPress.
        post_id (int): ID статьи.

    Returns:
        tuple: (HTML-контент статьи, данные из поля acf).
               Возвращает ("","") в случае ошибки.
    """
    try:
        api_url = f"{base_url}/wp-json/wp/v2/posts/{post_id}"
        logger.info(f"Запрос к API: {api_url}")
        response = _make_request(api_url)
        if response is None:
            return "", {}

        post_data: Dict[str, any] = response.json()
        content: str = post_data["content"]["rendered"]
        acf_data: Dict[str, any] = post_data.get("acf", {})  # Safely get 'acf' data

        return content, acf_data

    except KeyError as e:
        logger.error(f"Ошибка структуры JSON при получении контента статьи {post_id}: {e}", exc_info=True)
        return "", {}
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении контента статьи {post_id}: {e}", exc_info=True)
        return "", {}


def _make_request(url: str, max_attempts: int = 3) -> Optional[requests.Response]:
    """
    Выполняет HTTP-запрос с повторными попытками в случае ошибки.

    Args:
        url (str): URL для запроса.
        max_attempts (int): Максимальное количество попыток.

    Returns:
        requests.Response: Объект Response в случае успеха, None в случае неудачи после всех попыток.
    """
    for attempt in range(max_attempts):
        try:
            response: requests.Response = requests.get(url)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка при запросе {url} (попытка {attempt + 1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                sleep_time = 2 ** attempt  # Экспоненциальная задержка (1, 2, 4 секунды)
                logger.info(f"Повторная попытка через {sleep_time} секунд...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Не удалось получить данные после {max_attempts} попыток: {e}")
                return None  # Return None after all retries fail
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при запросе {url}: {e}", exc_info=True)
            return None

    return None


if __name__ == '__main__':
    # Пример использования (только для тестирования)
    from core.utils import setup_logger
    setup_logger()

    BASE_URL = "https://gomoscow.info"  # Замените на URL вашего сайта

    # Получение списка статей
    all_posts = get_all_posts(BASE_URL)
    if all_posts:
        logger.info(f"Найдено {len(all_posts)} статей.")
        # print(all_posts) # Вывод для отладки
    else:
        logger.warning("Не удалось получить список статей.")

    # Получение контента первой статьи (если есть статьи)
    if all_posts:
        first_post_id = all_posts[0]["id"]
        content, acf_data = get_post_content(BASE_URL, first_post_id)
        if content:
            logger.info(f"Контент первой статьи (ID {first_post_id}): {content[:200]}...")  # Вывод первых 200 символов
            logger.info(f"ACF Data первой статьи (ID {first_post_id}): {acf_data}")
        else:
            logger.warning(f"Не удалось получить контент статьи {first_post_id}.")