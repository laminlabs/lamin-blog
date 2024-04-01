# isort:skip_file
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

from lamin_sphinx import *  # noqa
from lamin_sphinx import html_theme_options, html_context  # noqa

project = "Lamin Blog"
html_title = f"{project}"
html_context["github_repo"] = "lamin-blog"  # noqa

ogp_site_url = "https://lamin.ai/blog"
ogp_site_name = project

html_theme_options["logo"] = {
    "link": ogp_site_url,
    "text": project,
    "root": "https://lamin.ai",
}
html_theme_options["icon_links"] = [
    {
        "name": "GitHub",
        "url": "https://github.com/laminlabs/lamin-blog",
        "icon": "fa-brands fa-github",
    },
]

# Blog

authors = {
    "bpenteado": ("Bernardo Penteado", "https://pbern.com"),
    "chaichontat": ("Chaichontat Sriworarat", "https://github.com/chaichontat"),
    "falexwolf": ("Alex Wolf", "https://falexwolf.me"),
    "felix-fischer*": ("Felix Fischer*", ""),
    "maciek-wiatrak": ("Maciek Wiatrak", ""),
    "ilan-gold": ("Ilan Gold", ""),
    "fabian-theis": ("Fabian Theis", ""),
    "jkobject": ("Jeremie Kalfon", "https://www.jkobject.com"),
    "yanay-rosen": ("Yanay Rosen", ""),
    "fredericenard": ("Frederic Enard", "https://github.com/fredericenard"),
    "Koncopd": ("Sergei Rybakov", "https://github.com/Koncopd"),
    "Koncopd*": ("Sergei Rybakov*", "https://github.com/Koncopd"),
    "sunnyosun": ("Sunny Sun", "https://github.com/sunnyosun"),
    "Zethson": ("Lukas Heumos", "https://github.com/Zethson"),
}

blog_baseurl = "https://lamin.ai/blog"
blog_post_pattern = "*"
blog_authors = authors
post_date_format = "%Y-%m-%d"
blog_path = "index"
