import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def parse_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    events = []
    event_elements = soup.find_all('div', class_='events-elem')

    if not event_elements:
        print("Не найдены элементы мероприятий.")
        return events

    for event in event_elements:
        title_tag = event.find('a', class_='title')
        date_tag = event.find('div', class_='date')
        link_tag = event.find('a', class_='title')
        price_tag = event.find('div', class_='price')
        image_tag = event.find('img')

        if title_tag and date_tag and link_tag:
            title = title_tag.text.strip()
            date = date_tag.text.strip()
            link = urljoin(url, link_tag['href'])
            price = price_tag.text.strip() if price_tag else None
            image_url = urljoin(url, image_tag['src']) if image_tag else None
            events.append({'title': title, 'date': date, 'link': link, 'price': price, 'image_url': image_url})
        else:
            print("Не удалось извлечь данные из элемента мероприятия.")

    return events

if __name__ == "__main__":
    events = parse_events('https://mgn.afishagoroda.ru/events')
    if events:
        for event in events:
            print(event)
    else:
        print("Не найдено мероприятий.")
