# isort:skip_file
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

from lamin_sphinx import *  # noqa
from lamin_sphinx import authors, html_theme_options, html_context  # noqa

project = "Lamin Blog"
html_title = f"{project}"
html_context["github_repo"] = "lamin-blog"  # noqa

ogp_site_url = "https://lamin.ai/blog"
ogp_site_name = project

# Blog
blog_baseurl = "https://lamin.ai/blog"
blog_post_pattern = "2022/*"
blog_authors = authors
post_date_format = "%Y-%m-%d"
blog_path = "index"
