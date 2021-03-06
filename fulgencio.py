"""
Gets lots of job vacancies!
Writes them in leads.xlsx
"""

import time
import re
import pandas as pd
import os
from decouple import config
import values
import util

EMAIL_ID = 'email'
PASS_ID = 'pass'
LOGIN_BUTTON_ID = 'u_0_2'
SCROLL_SCREENS = 1
SCREEN_HEIGHT = 1080
COORDINATES = (int(config('coordinate_x')), int(config('coordinate_y')))
COLUMNS = ['post', 'word', 'group_name', 'group_url', 'count']
MAIN_URL = config('main_url')


def get_profile(split):
    closest_math = [m.start() for m in re.finditer(MAIN_URL, split)]
    if len(closest_math) > 0:
        closest_math = closest_math[-1]
        almost = split[closest_math:]
    else:
        return None

    pattern = f'{MAIN_URL}\S*'
    return re.search(pattern, almost).group()


def filter_posts_with_email(df):
    return df[df['post'].str.contains('@')]


def scrap_word(word, df, html, group_name, group_url):
    """
    :param word: string
    :param df: pandas Dataframe
    :param html: str html
    :param group_url: str
    :return: df
    """

    post_pattern = f'>[^>]*\s{word}\s[^<]*<'
    splits = re.compile(post_pattern).split(html)[:-1]

    # found nothing
    if len(splits) == 0:
        print(f'nothing found :( for word {word} on group {group_url}')
        return df

    posts = re.findall(post_pattern, html)
    for idx, split in enumerate(splits):
        profile = get_profile(split)
        if profile and MAIN_URL in profile:
            post = posts[idx].replace('>', '').replace('<', '')
            if profile in list(df.index.values):
                if post == df.loc[profile, 'post']:
                    df.loc[profile, 'count'] += 1
                else:
                    df.loc[profile, 'post'] += post
            else:

                row = pd.Series({'post': post,
                                 'word': word,
                                 'group_name': group_name,
                                 'group_url': group_url,
                                 'count': 1}, name=profile)

                df = df.append(row)

    return filter_posts_with_email(df)


def scroll_down(group_name, scroll_steps, browser):
    for i in range(scroll_steps):
        height = SCREEN_HEIGHT * SCROLL_SCREENS
        browser.execute_script(f'window.scrollTo({i * height}, {(i + 1) * height})')

        # TODO: make this work
        browser.save_screenshot(os.path.join('images', f'{group_name}_{i}.png'))
        time.sleep(0.3)


def save_and_get_html(browser):
    html = browser.page_source.lower()
    with open('page.html', 'w', encoding='utf-8') as f:
        f.write(html)

    return html


def get_file(name):
    with open(name, 'rb', encoding='utf-8') as my_file:
        return my_file.readlines()


def scrape_all(browser):
    results = pd.DataFrame(columns=COLUMNS)

    for idx, (group_name, group_url, scroll_steps) in enumerate(values.get_groups()):

        browser.get(group_url)

        scroll_down(group_name, scroll_steps, browser)
        html = save_and_get_html(browser)

        for word in values.get_keywords():
            results = scrap_word(word=word.lower().replace('\n', ''),
                                 df=results,
                                 html=html,
                                 group_url=group_url,
                                 group_name=group_name)

        # Save partial result
        results.sort_values(by='count', ascending=False).to_excel('leads.xlsx')

    return results


if __name__ == '__main__':
    scrape_all(util.load_browser_and_login())
