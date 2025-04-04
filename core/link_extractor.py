# core/link_extractor.py

import re  # Import the re module
import requests  # Import requests module
import logging
import time
from core.utils import get_logger
from urllib.parse import urlparse, ParseResult
from typing import List, Dict, Optional, Union

logger = get_logger(__name__)


def extract_internal_links(post_content: str, base_url: str) -> List[str]:
    """
    Извлекает внутренние ссылки (с учетом конечного слеша).
    """
    try:
        escaped_base_url: str = re.escape(base_url.rstrip('/'))
        regex: str = f'<a href="(?:https?://)?(?:www\\.)?{escaped_base_url}([^"]*?)".*?>'
        links: List[str] = re.findall(regex, post_content, re.IGNORECASE)

        internal_links: List[str] = []
        for link in links:
            parsed_url: ParseResult = urlparse(link)
            path: str = parsed_url.path
            if path.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif')):
                # Skip links to files
                continue
            slug: str = path.strip('/').split('/')[-1]  # Remove trailing slash first
            internal_links.append(slug)
        return internal_links
    except Exception as e:
        logger.error(f"Ошибка при извлечении ссылок: {e}")
        return []


def extract_acf_links(acf_data: Dict, acf_field_name: str = "related-posts") -> List[int]:
    """
    Извлекает ID статей из поля related-posts в данных acf.

    Args:
        acf_data (dict): Данные из поля acf.
        acf_field_name (str):  Название поля ACF, содержащего список связанных статей.

    Returns:
        list: Список ID статей, на которые ссылается эта статья (из acf).
              Возвращает пустой список в случае ошибки или отсутствия данных.
    """
    try:
        related_posts: Optional[Union[List[Union[int, str]], str]] = acf_data.get(acf_field_name)
        if isinstance(related_posts, str):
            # пробуем преобразовать строку в список id через запятую
            related_posts_list: List[str] = [x.strip() for x in related_posts.split(',') if x.strip().isdigit()]
            related_posts: List[int] = [int(x) for x in related_posts_list if x.isdigit()]
        elif isinstance(related_posts, list):
            # Преобразуем элементы списка в целые числа, если это возможно
            related_posts = [int(x) for x in related_posts if isinstance(x, (int, str)) and str(x).isdigit()]
        else:
            return []

        # Фильтруем None значения и возвращаем список ID статей
        return [post_id for post_id in related_posts if post_id is not None]
    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"Ошибка при извлечении ссылок из ACF: {e}")
        return []


def resolve_slug_to_id(base_url: str, slug: str, ignore_non_posts: bool = True, max_attempts: int = 3) -> Optional[int]:
    """
    По slug пытается получить id поста, страницы или категории.
    Args:
        base_url (str): Базовый URL сайта WordPress.
        slug (str): Slug статьи, страницы или категории.
        ignore_non_posts (bool):  Нужно ли игнорировать страницы и категории
        max_attempts (int): Максимальное количество попыток.
    Returns:
        int: ID поста, страницы или категории. Возвращает None, если не найдено.
    """
    for attempt in range(max_attempts):
        try:
            # Try to get post by slug
            api_url: str = f"{base_url}/wp-json/wp/v2/posts?slug={slug}"
            response = requests.get(api_url)
            response.raise_for_status()
            posts: List[Dict] = response.json()
            if posts:
                return posts[0]["id"]

            if not ignore_non_posts:
                # Try to get page by slug
                api_url = f"{base_url}/wp-json/wp/v2/pages?slug={slug}"
                response = requests.get(api_url)
                response.raise_for_status()
                pages: List[Dict] = response.json()
                if pages:
                    return pages[0]["id"]

                # Try to get category by slug
                api_url = f"{base_url}/wp-json/wp/v2/categories?slug={slug}"
                response = requests.get(api_url)
                response.raise_for_status()
                categories: List[Dict] = response.json()
                if categories:
                    return categories[0]["id"]

            logger.warning(f"Не удалось найти ID для slug '{slug}'.")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении ID для slug '{slug}' (попытка {attempt + 1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                sleep_time: int = 2 ** attempt  # Экспоненциальная задержка (1, 2, 4 секунды)
                logger.info(f"Повторная попытка через {sleep_time} секунд...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Не удалось получить данные после {max_attempts} попыток: {e}")
                return None
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при запросе {url}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    # Пример использования (только для тестирования)
    from core.utils import setup_logger
    setup_logger()

    # Пример данных ACF
    ACF_DATA: Dict = {
        "related-posts": [123, 456, 789, "1011"],
        "some_other_field": "some_value"
    }

    # Извлечение ссылок
    acf_links: List[int] = extract_acf_links(ACF_DATA)
    logger.info(f"Ссылки из ACF: {acf_links}")

    ACF_DATA_STRING: Dict = {
        "related-posts": "123, 456, 789, 1011",
        "some_other_field": "some_value"
    }

    acf_links_string: List[int] = extract_acf_links(ACF_DATA_STRING)
    logger.info(f"Ссылки из ACF (string): {acf_links_string}")

    # Пример использования resolve_slug_to_id
    BASE_URL: str = "https://gomoscow.info"  # Замените на URL вашего сайта для тестов
    slug_to_resolve: str = "vdnh"  # Замените на существующий slug для тестов
    post_id: Optional[int] = resolve_slug_to_id(BASE_URL, slug_to_resolve)

    if post_id:
        logger.info(f"ID для slug '{slug_to_resolve}': {post_id}")
    else:
        logger.warning(f"Не удалось определить ID для slug '{slug_to_resolve}'.")