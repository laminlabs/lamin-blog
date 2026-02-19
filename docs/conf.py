# isort:skip_file
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

from lamin_sphinx import *  # noqa
from lamin_sphinx import html_theme_options, html_context, extensions  # type: ignore[attr-defined]  # noqa
import lndocs  # noqa

project = "Lamin Blog"
html_title = f"{project}"
html_context["github_repo"] = "lamin-blog"  # noqa

ogp_site_url = "https://blog.lamin.ai"
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

extensions.append("ablog")
authors = {
    "chaichontat": ("Chaichontat Sriworarat", "https://github.com/chaichontat"),
    "falexwolf": ("Alex Wolf", "https://falexwolf.me"),
    "felix-fischer": ("Felix Fischer", "https://github.com/felix0097"),
    "keller-mark": ("Mark Keller", "https://github.com/keller-mark"),
    "maciek-wiatrak": ("Maciek Wiatrak", "https://github.com/macwiatrak"),
    "ilan-gold": ("Ilan Gold", "https://github.com/ilan-gold"),
    "fabian-theis": (
        "Fabian Theis",
        "https://scholar.google.com/citations?user=sqWpn2AAAAAJ&hl=en",
    ),
    "jkobject": ("Jeremie Kalfon", "https://www.jkobject.com"),
    "yanay-rosen": ("Yanay Rosen", "https://twitter.com/YanayRosen"),
    "fredericenard": ("Frederic Enard", "https://github.com/fredericenard"),
    "Koncopd": ("Sergei Rybakov", "https://github.com/Koncopd"),
    "sunnyosun": ("Sunny Sun", "https://github.com/sunnyosun"),
    "Zethson": ("Lukas Heumos", "https://github.com/Zethson"),
    "treis-tim": ("Tim Treis", "https://github.com/timtreis"),
    "marconato-luca": ("Luca Marconato", "https://github.com/LucaMarconato"),
    "zimmermann-lea": ("Lea Zimmermann", "https://github.com/zimea"),
    "namsaraeva-altana": ("Altana Namsaraeva", "https://github.com/namsaraeva"),
    "vierdag-michiel": ("Wouter-Michiel Vierdag", "https://github.com/melonora"),
}
lndocs.authors = authors

blog_baseurl = "https://blog.lamin.ai"
blog_post_pattern = "*"
blog_authors = authors.copy()
blog_authors.update({f"{k}*": v for k, v in authors.items()})
post_date_format = "%Y-%m-%d"
blog_path = "index"
