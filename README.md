# zendesk-help-center-export
This script will allow you to export the full Zendesk help center experience to static HTML (minus dynamic elements, like search and recent articles), optimized for jekyll.

## Quickstart
```
pip install -r requirements.txt
python export.py --subdomain=yourSubdomain --username=youremail@email.com --password=yourPassword --templates-dir=example/export-templates/ --blacklist=example/blacklist.yml hc/en-us/
```

## Usage
First, go through your categories, sections, and articles, and make note of which ones you don't want to export. Add the ids of these to your blacklist.yml. For an example, see examples/blacklist.yml

Next, download an example article, category, and section html file. You'll make a template out of each of these, using [jinja2](http://jinja.pocoo.org/). For an example template of each of the three pages, see example/export-templates. 

You'll also want to download any other necessary files - css, favicon, fonts, and javascript. For an example of what css/js is actually needed, take a look at example/export-templates/header.html and example/export-templates/footer.html.

Finally, go through each article, and download any images or other article attachments (embedded content is fine).

Run the export, which will dump a bunch of html documents to the export path, in a way that allows jekyll to serve them in the same manner as they were served on Zendesk.

Depending on your use case, you may want to relativize all paths - for example, changing support.mydomain.com/hc/en-us/... to /hc/en-us/...

## CLI
```
usage: export.py [-h] --subdomain SUBDOMAIN --username USERNAME --password
                 PASSWORD --templates-dir TEMPLATES_DIR
                 [--article-template ARTICLE_TEMPLATE]
                 [--section-template SECTION_TEMPLATE]
                 [--category-template CATEGORY_TEMPLATE]
                 [--index-template INDEX_TEMPLATE] [--blacklist BLACKLIST]
                 exportpath

positional arguments:
  exportpath

optional arguments:
  -h, --help            show this help message and exit
  --subdomain SUBDOMAIN
                        Zendesk subdomain
  --username USERNAME   Zendesk username
  --password PASSWORD   Zendesk password
  --templates-dir TEMPLATES_DIR
                        directory for jinja2 templates
  --article-template ARTICLE_TEMPLATE
                        Jinja2 template for articles, in templates-dir
  --section-template SECTION_TEMPLATE
                        Jinja2 template for sections, in templates-dir
  --category-template CATEGORY_TEMPLATE
                        Jinja2 template for categories, in templates-dir
  --index-template INDEX_TEMPLATE
                        Jinja2 template for index, in templates-dir
  --blacklist BLACKLIST
                        yml file of blacklisted categories, sections, or
                        articles
```

## Known Issues
Currently, this script only downloads the en-us locale. In addition, it doesn't download any article attachments, css, js, or fonts - you'll need to download all of those yourself. Zendesk allows links to either be the bare id (eg /hc/en-us/articles/1234) or the id and a name slug (eg /hc/en-us/articles/1234-my-name-here-). This export only supports the latter type of link, so you'll need to fix up any links that look like the former.

## Todo
- [ ] Support locales
- [ ] Support article attachments
- [ ] Support URL rewriting
