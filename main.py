# main.py

import pandas as pd
import logging
from core.utils import setup_logger, get_logger
from core.api_client import get_all_posts, get_post_content
from core.link_extractor import extract_internal_links, extract_acf_links, resolve_slug_to_id
from config import SITES, CSV_FILENAME, ACF_FIELD_NAME, IGNORE_NON_POSTS
from core.data_processor import calculate_incoming_links, build_dataframe
from typing import List, Dict, Any, Optional

setup_logger()  # Настраиваем логгер
logger = get_logger(__name__)


def main() -> None:
    """
    Основная функция для запуска анализа внутренних ссылок для нескольких сайтов и экспорта результатов в CSV.
    """
    try:
        logger.info("Начинаем анализ внутренних ссылок для нескольких сайтов...")

        # Loop through each site in the SITES list
        for site in SITES:
            base_url: str = site["url"]
            site_name: str = site["name"]
            csv_filename: str = CSV_FILENAME.format(site_name=site_name)  # Format the filename
            acf_field_name: str = site.get("acf_field_name", ACF_FIELD_NAME)
            ignore_non_posts: bool = site.get("ignore_non_posts", IGNORE_NON_POSTS)

            logger.info(f"Анализ сайта: {base_url}")

            # 1. Получение списка всех статей
            logger.info(f"Получение списка статей с сайта: {base_url}")
            all_posts: List[Dict[str, Any]] = get_all_posts(base_url)

            if not all_posts:
                logger.error(f"Не удалось получить список статей с сайта {base_url}.  Переход к следующему сайту.")
                continue  # Skip to the next site

            logger.info(f"Найдено {len(all_posts)} статей на сайте {base_url}.")

            # 2. Извлечение внутренних ссылок из контента каждой статьи
            logger.info(f"Извлечение внутренних ссылок из контента статей на сайте {base_url}...")
            links_per_post: Dict[int, List[int]] = {}
            for post in all_posts:
                post_id: int = post['id']
                post_content: str
                acf_data: Dict[str, Any]
                post_content, acf_data = get_post_content(base_url, post_id)

                internal_links: List[str] = []
                if post_content:
                    internal_links = extract_internal_links(post_content, base_url)
                else:
                    logger.warning(f"Не удалось получить контент статьи {post_id}.")

                acf_links: List[int] = []
                if acf_data:
                    acf_links = extract_acf_links(acf_data, acf_field_name)
                else:
                    logger.warning(f"Не удалось получить ACF data для статьи {post_id}.")

                # Объединяем ссылки из контента и ACF
                all_links: List[Any] = internal_links + acf_links

                # Convert slugs to post IDs:
                links_per_post[post_id] = []
                for link in all_links:
                    linked_post_id: Optional[int] = None
                    if isinstance(link, int):
                        linked_post_id = link  # Если это ID, то используем его напрямую
                    else:
                        # Если это slug, пытаемся найти ID
                        linked_post_id = resolve_slug_to_id(base_url, link, ignore_non_posts)

                    if linked_post_id:
                        if linked_post_id in [p['id'] for p in all_posts] or not ignore_non_posts:
                            links_per_post[post_id].append(linked_post_id)
                        else:
                            logger.warning(
                                f"ID {linked_post_id} не принадлежит статье.  Возможно, это страница или категория, и IGNORE_NON_POSTS = True. Ссылка на  '{link}' в статье {post_id} пропущена.")
                    else:
                        logger.warning(
                            f"Не удалось найти статью, страницу или категорию с slug '{link}', на которую ссылается статья {post_id}")

                # logger.info(f"Статья {post_id}: {links_per_post.get(post_id, [])}") # Для отладки

            # 3. Вычисление входящих ссылок
            logger.info(f"Вычисление входящих ссылок на сайте {base_url}...")
            incoming_links: Dict[int, List[int]] = calculate_incoming_links(all_posts, links_per_post)

            # 4. Построение DataFrame
            logger.info(f"Построение DataFrame для сайта {base_url}...")
            df: pd.DataFrame = build_dataframe(all_posts, links_per_post, incoming_links)

            # 5. Экспорт DataFrame в CSV
            logger.info(f"Экспорт DataFrame в CSV файл: {csv_filename}")
            df.to_csv(csv_filename, index=False, sep=";", encoding="utf-8")

            logger.info(f"Анализ сайта {base_url} завершен.")

        logger.info("Анализ внутренних ссылок для всех сайтов завершен успешно.")

    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()