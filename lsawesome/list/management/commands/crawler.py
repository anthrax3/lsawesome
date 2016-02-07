from django.core.management.base import BaseCommand
from gittle import Gittle
import mistune
from bs4 import BeautifulSoup
from os import path


class Command(BaseCommand):
    help = 'Clones upstream and all lists repositories'
    upstream = 'https://github.com/sindresorhus/awesome.git'
    dir_base = '/tmp/lsawesome'

    def find_readme(self, base_path):
        if path.isfile(path.join(base_path, 'readme.md')):
            return 'readme.md'
        elif path.isfile(path.join(base_path, 'README.md')):
            return 'README.md'
        elif path.isfile(path.join(base_path, 'README.md')):
            return 'README.md'

        return None

    def real_upstream(self):
        upstream_path = path.join(self.dir_base, 'upstream')

        # cloning the repository
        Gittle.clone(self.upstream, upstream_path)

        readme_file = self.find_readme(upstream_path)

        with open(path.join(upstream_path, readme_file)) as f:
            soup = BeautifulSoup(mistune.markdown(f.read()), 'html.parser')
            print(soup)

        self.stdout.write(self.style.SUCCESS('Successfully read the upstream'))

    def handle(self, *args, **options):
        # step 1: clone and read the upstream's README file
        self.real_upstream()
