from django.core.management.base import BaseCommand
from gittle import Gittle
import mistune
from urlparse import urlparse
from bs4 import BeautifulSoup
from os import path
from slugify import slugify
from list.models import Category, List, Item
import uuid


class Command(BaseCommand):
    help = 'Clones upstream and all lists repositories'
    upstream = 'https://github.com/sindresorhus/awesome.git'
    dir_base = '/tmp/lsawesome'

    def find_readme(self, base_path, search_path=None):

        if search_path is not None and path.isfile(path.join(base_path, search_path)):
            return search_path
        elif path.isfile(path.join(base_path, 'readme.md')):
            return 'readme.md'
        elif path.isfile(path.join(base_path, 'README.md')):
            return 'README.md'
        elif path.isfile(path.join(base_path, 'README.MD')):
            return 'README.MD'

        return None

    # finds all ULs and LIs and save them
    def save_md(self, soup, is_upstream, ls):
        for ul in soup.find_all('ul', recursive=False):
            self.save_ul(ul, is_upstream, None, None, ls)

    def save_ul(self, ul, is_upstream, current_category=None, parent_category=None, ls=None):
        category = None

        if current_category is not None:
            category = current_category
        else:
            # find the category
            for sibling in ul.previous_siblings:
                if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                    category = sibling.get_text()
                    break

        if category is not None:
            category_obj = Category.objects.get_or_create(slug=slugify(category), name=category, parent=parent_category[0] if parent_category is not None else None)

            for child in ul.children:
                if child.name == 'li':
                    self.save_li(child, is_upstream, category_obj, ls)


    def save_li(self, child, is_upstream, parent_category, ls):
        # let's find the inside anchor link
        anchor = child.find('a')
        ul_childs = child.find_all('ul')

        if anchor:
            href = urlparse(anchor.attrs['href'])

            # to avoid `#` links
            if href.netloc == 'github.com':
                print(anchor, href, is_upstream)

                if is_upstream:
                    ls = List(category=parent_category[0], github=anchor.attrs['href'], name=anchor.get_text(), slug=slugify(anchor.get_text()))

                    ls.save()

                    self.read_repo(str(anchor.attrs['href']) + '.git', ls)
                else:
                    parsed_url = urlparse(anchor.attrs['href'])

                    if parsed_url.path != '':
                        Item(ls=ls, github=anchor.attrs['href'], name=anchor.get_text(), slug=slugify(parsed_url.path.split('/')[1] + '-' + anchor.get_text())).save()

            if len(ul_childs) > 0:
                for ul_child in ul_childs:
                    self.save_ul(ul_child, is_upstream, anchor.get_text(), parent_category, ls)


    # clones the upstream and save all items with their category
    def read_repo(self, git=None, ls=None):
        clone_path = path.join(self.dir_base, str(uuid.uuid4()) if git is not None else 'upstream')

        print('github url', git if git is not None else self.upstream)

        git_url = urlparse(git if git is not None else self.upstream)
        clone_url = None
        splitted_path = git_url.path.strip('/').split('/')

        if len(splitted_path) > 2:
            clone_url = git_url.scheme + '://' + git_url.netloc + '/' + splitted_path[0] + '/' + splitted_path[1] + '.git'
        else:
            clone_url = git if git is not None else self.upstream

        print('clone url', clone_url)

        # cloning the repository
        Gittle.clone(clone_url, clone_path)

        if len(splitted_path) > 2:
            readme_file = self.find_readme(clone_path, '/'.join(str(x) for x in splitted_path[2:]))
        else:
            readme_file = self.find_readme(clone_path)

        print(clone_url, readme_file)

        try:
            with open(path.join(clone_path, readme_file)) as f:
                soup = BeautifulSoup(mistune.markdown(f.read()), 'html.parser')

                self.save_md(soup, True if git is None else False, ls)

            self.stdout.write(self.style.SUCCESS('Successfully read the upstream'))
        except Exception as exp:
            print('An error happened while reading the repo.', exp)

    def handle(self, *args, **options):
        # step 1: clone and read the upstream's README file
        self.read_repo()
