import argparse
import os
import sys
import urlparse

import jinja2
import requests
import yaml

credentials = 'your_zendesk_email', 'your_zendesk_password'
zendesk = 'https://your_subdomain.zendesk.com'
language = 'some_locale'


def ensuredir(dir_name):
    try:
        os.makedirs(dir_name)
    except OSError:
        if not os.path.isdir(dir_name):
            raise


class ZendeskApi(object):
    def __init__(self, subdomain, credentials, locale='en-us'):
        self._credentials = credentials
        self._base_url = 'https://{0}.zendesk.com/api/v2/help_center/{1}'.format(subdomain, locale)

    def _path(self, request_path):
        return '{0}/{1}'.format(self._base_url, request_path)

    def _paginate(self, endpoint, handler):
        while endpoint:
            response = requests.get(endpoint, auth=self._credentials)
            if response.status_code != 200:
                print('Failed to retrieve page from {}, with error {}'.format(endpoint, response.status_code))
                raise IOError()

            data = response.json()
            handler(data)

            endpoint = data['next_page']

    def get_categories(self):
        categories = []
        endpoint = self._path('categories.json')

        def handle_response(data):
            for category in data['categories']:
                categories.append(category)

        self._paginate(endpoint, handle_response)
        return categories

    def get_sections_in_category(self, category_id):
        sections = []
        endpoint = self._path('categories/{0}/sections.json'.format(category_id))

        def handle_response(data):
            for section in data['sections']:
                sections.append(section)

        self._paginate(endpoint, handle_response)
        return sections

    def get_articles_in_section(self, section_id):
        articles = []
        endpoint = self._path('sections/{0}/articles.json'.format(section_id))

        def handle_response(data):
            for article in data['articles']:
                articles.append(article)

        self._paginate(endpoint, handle_response)
        return articles


class ZendeskExportRun(object):
    def __init__(self, backup_path, zendesk_api, templates_dir, templates, blacklist=None):
        self.backup_path = backup_path
        ensuredir(backup_path)

        self._zendesk_api = zendesk_api

        self.blacklist = blacklist
        if not self.blacklist:
            self.blacklist = {
                'articles': [],
                'sections': [],
                'categories': []
            }

        def relative_url(value):
            return urlparse.urlparse(value).path

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=jinja2.select_autoescape(['html'])
        )
        env.filters['relative_url'] = relative_url

        self._templates = {k: env.get_template(v) for k, v in templates.iteritems()}

    def export(self):
        categories = [category for category in self._zendesk_api.get_categories() if
                      category['id'] not in self.blacklist['categories']]

        for category in categories:
            sections = [section for section in self._zendesk_api.get_sections_in_category(category['id']) if
                        section['id'] not in self.blacklist['sections']]
            for section in sections:
                articles = [article for article in self._zendesk_api.get_articles_in_section(section['id']) if
                            article['id'] not in self.blacklist['articles']]
                section['articles'] = articles

            self._write_category_page(category, sections)

            for section in sections:
                self._export_section(section, sections, category)

        write_page(self._templates['index'], {
            'name': '',
            'html_url': '',
            'categories': categories
        }, self.backup_path)

        return 0

    def _export_section(self, section, sections, category):
        self._write_section_page(section, sections, category)

        for article in section['articles']:
            self._write_article_page(article, section, sections, category)

    def _write_category_page(self, category, sections):
        category_path = os.path.join(self.backup_path, 'categories',
                                     '{0}'.format(category['html_url'].rsplit('/', 1)[-1]))
        write_page(self._templates['category'], {
            'name': category['name'],
            'html_url': category['html_url'],
            'sections': sections
        }, category_path)

    def _write_article_page(self, article, section, sections, category):
        article_path = os.path.join(self.backup_path, 'articles', '{0}'.format(article['html_url'].rsplit('/', 1)[-1]))
        write_page(self._templates['article'], {
            'name': article['name'],
            'html_url': article['html_url'],
            'body': article['body'],
            'my_section': section,
            'sections': sections,
            'category': category
        }, article_path)

    def _write_section_page(self, section, sections, category):
        section_path = os.path.join(self.backup_path, 'sections', '{0}'.format(section['html_url'].rsplit('/', 1)[-1]))
        write_page(self._templates['section'], {
            'id': section['id'],
            'name': section['name'],
            'articles': section['articles'],
            'sections': sections,
            'category': category,
        }, section_path)


def write_page(template, template_payload, path):
    ensuredir(path)

    rendered_template = template.render(template_payload)

    with open(os.path.join(path, 'index.html'), 'w') as f:
        f.write(rendered_template.encode('utf-8'))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--subdomain', required=True, help='Zendesk subdomain')
    parser.add_argument('--username', required=True, help='Zendesk username')
    parser.add_argument('--password', required=True, help='Zendesk password')
    parser.add_argument('--templates-dir', required=True, help='directory for jinja2 templates')
    parser.add_argument('--article-template', default='article.html',
                        help='Jinja2 template for articles, in templates-dir')
    parser.add_argument('--section-template', default='section.html',
                        help='Jinja2 template for sections, in templates-dir')
    parser.add_argument('--category-template', default='category.html',
                        help='Jinja2 template for categories, in templates-dir')
    parser.add_argument('--index-template', default='index.html', help='Jinja2 template for index, in templates-dir')
    parser.add_argument('--blacklist', type=argparse.FileType('r'),
                        help='yml file of blacklisted categories, sections, or articles')
    parser.add_argument('exportpath')

    args = parser.parse_args(sys.argv[1:])
    return args


if __name__ == '__main__':
    args = parse_args()

    templates = {
        'article': args.article_template,
        'section': args.section_template,
        'category': args.category_template,
        'index': args.index_template
    }

    blacklist = None
    if args.blacklist:
        blacklist = yaml.load(args.blacklist)

    zendesk_api = ZendeskApi(args.subdomain, (args.username, args.password))
    run = ZendeskExportRun(args.exportpath, zendesk_api, args.templates_dir, templates, blacklist)

    sys.exit(run.export())
