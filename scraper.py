import logging
import requests
from normality import collapse_spaces, stringify
from urlparse import urljoin
from lxml import html

from libsanctions import Source, make_uid

log = logging.getLogger(__name__)
URL = 'https://www.cia.gov/library/publications/resources/world-leaders-1/index.html'  # noqa


def element_text(el):
    if el is None:
        return
    text = stringify(el.text_content())
    if text is not None:
        return collapse_spaces(text)


def parse_entity(source, url, country, component, row, updated_at):
    function = element_text(row.find('.//span[@class="title"]'))
    if function is None:
        return
    name = element_text(row.find('.//span[@class="cos_name"]'))
    if name is None:
        return

    uid = make_uid(country, name, function)
    entity = source.create_entity(uid)
    entity.name = name
    entity.type = entity.TYPE_INDIVIDUAL
    entity.function = function
    entity.url = url
    entity.updated_at = updated_at
    nationality = entity.create_nationality()
    nationality.country = country
    entity.save()


def scrape_country(source, country_url, country_name):
    res = requests.get(country_url)
    doc = html.fromstring(res.content)
    updated_at = doc.findtext('.//span[@id="lastUpdateDate"]')
    output = doc.find('.//div[@id="countryOutput"]')
    if output is None:
        return
    component = None
    for row in output.findall('.//li'):
        next_comp = row.findtext('./td[@class="componentName"]/strong')
        if next_comp is not None:
            component = next_comp
            continue
        parse_entity(source, country_url, country_name, component,
                     row, updated_at)


def scrape():
    res = requests.get(URL)
    doc = html.fromstring(res.content)
    source = Source('us-cia-world-leaders')

    for link in doc.findall('.//div[@id="cosAlphaList"]//a'):
        url = urljoin(URL, link.get('href'))
        log.info("Crawling country: %s", link.text)
        scrape_country(source, url, link.text)

    source.finish()


if __name__ == '__main__':
    scrape()
