# core/data_processor.py

import pandas as pd
import logging
from typing import List, Dict, Any
from core.utils import get_logger

logger = get_logger(__name__)


def calculate_incoming_links(all_posts: List[Dict[str, Any]], links_per_post: Dict[int, List[int]]) -> Dict[int, List[int]]:
    """
    Вычисляет входящие ссылки для каждой статьи.

    Args:
        all_posts (list): Список словарей с информацией о всех статьях (id, slug).
        links_per_post (dict): Словарь, где ключ - ID статьи, значение - список ID статей, на которые она ссылается.

    Returns:
        dict: Словарь, где ключ - ID статьи, значение - список ID статей, которые на нее ссылаются.
    """
    incoming_links: Dict[int, List[int]] = {}
    for post in all_posts:
        incoming_links[post['id']] = []  # Initialize empty list for each post

    for post_id, outgoing_links in links_per_post.items():
        for linked_post_id in outgoing_links:
            if linked_post_id in incoming_links:
                incoming_links[linked_post_id].append(post_id)
            else:
                logger.warning(f"Статья {linked_post_id} не найдена в списке статей.")

    return incoming_links


def build_dataframe(all_posts: List[Dict[str, Any]], links_per_post: Dict[int, List[int]], incoming_links: Dict[int, List[int]]) -> pd.DataFrame:
    """
    Строит DataFrame с информацией о статьях и их связях.

    Args:
        all_posts (list): Список словарей с информацией о всех статьях (id, slug).
        links_per_post (dict): Словарь, где ключ - ID статьи, значение - список ID статей, на которые она ссылается.
        incoming_links (dict): Словарь, где ключ - ID статьи, значение - список ID статей, которые на нее ссылаются.

    Returns:
        pandas.DataFrame: DataFrame с колонками: post_id, post_slug, outgoing_count, outgoing_links, incoming_count, incoming_links.
    """

    data: List[Dict[str, Any]] = []
    for post in all_posts:
        post_id: int = post['id']
        outgoing_links: List[int] = links_per_post.get(post_id, [])
        incoming_links_for_post: List[int] = incoming_links.get(post_id, [])

        data.append({
            'post_id': post_id,
            'post_slug': post['slug'],
            'outgoing_count': len(outgoing_links),
            'outgoing_links': ", ".join(map(str, outgoing_links)),  # Convert list of ints to comma-separated string
            'incoming_count': len(incoming_links_for_post),
            'incoming_links': ", ".join(map(str, incoming_links_for_post))  # Convert list of ints to comma-separated string
        })

    df: pd.DataFrame = pd.DataFrame(data)
    df = df.sort_values(by='incoming_count', ascending=False)  # Сортировка по incoming_count по убыванию
    return df


if __name__ == '__main__':
    # Пример использования (только для тестирования)
    from core.utils import setup_logger
    setup_logger()

    # Sample data (replace with actual data from your WordPress site)
    ALL_POSTS: List[Dict[str, Any]] = [
        {'id': 1, 'slug': 'главная-страница'},
        {'id': 2, 'slug': 'о-нас'},
        {'id': 3, 'slug': 'услуги'},
        {'id': 4, 'slug': 'контакты'}
    ]

    LINKS_PER_POST: Dict[int, List[int]] = {
        1: [2, 3],  # Главная страница ссылается на "О нас" и "Услуги"
        2: [4],  # "О нас" ссылается на "Контакты"
        3: [],  # "Услуги" не ссылается ни на что
        4: [1]  # "Контакты" ссылается на главную страницу
    }

    incoming_links: Dict[int, List[int]] = calculate_incoming_links(ALL_POSTS, LINKS_PER_POST)
    logger.info(f"Входящие ссылки: {incoming_links}")

    df: pd.DataFrame = build_dataframe(ALL_POSTS, LINKS_PER_POST, incoming_links)
    logger.info("DataFrame:")
    print(df.to_string())  # Выводим DataFrame в консоль