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
    "link": "/",
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
extensions.append("sphinxcontrib.mermaid")
authors = {
    "andreassteffen": ("Andreas Steffen", "https://github.com/andreassteffen"),
    "ap-dash": ("Andreas Poehlmann", "https://github.com/ap--"),
    "chaichontat": ("Chaichontat Sriworarat", "https://github.com/chaichontat"),
    "fabian-theis": (
        "Fabian Theis",
        "https://scholar.google.com/citations?user=sqWpn2AAAAAJ&hl=en",
    ),
    "falexwolf": ("Alex Wolf", "https://falexwolf.com"),
    "felix-fischer": ("Felix Fischer", "https://github.com/felix0097"),
    "fredericenard": ("Frederic Enard", "https://github.com/fredericenard"),
    "ilan-gold": ("Ilan Gold", "https://github.com/ilan-gold"),
    "ishitajain9717": ("Ishita Jain", "https://github.com/ishitajain9717"),
    "jejomath": ("Jesse Johnson", "https://github.com/jejomath"),
    "jkobject": ("Jeremie Kalfon", "https://www.jkobject.com"),
    "jpfeuffer": ("Julian Pfeuffer", "https://github.com/jpfeuffer"),
    "keller-mark": ("Mark Keller", "https://github.com/keller-mark"),
    "Koncopd": ("Sergei Rybakov", "https://github.com/Koncopd"),
    "lazappi": ("Luke Zappia", "https://github.com/lazappi"),
    "LucaMarconato": ("Luca Marconato", "https://github.com/LucaMarconato"),
    "maciek-wiatrak": ("Maciek Wiatrak", "https://github.com/macwiatrak"),
    "melonora": ("Wouter-Michiel Vierdag", "https://github.com/melonora"),
    "namsaraeva": ("Altana Namsaraeva", "https://github.com/namsaraeva"),
    "rcannood": ("Robrecht Cannoodt", "https://github.com/rcannood"),
    "sunnyosun": ("Sunny Sun", "https://github.com/sunnyosun"),
    "SZhengP": ("Shijie Zheng", "https://github.com/SZhengP"),
    "tgelafr-pfzr": ("Tatiana Gelaf Romer", "https://github.com/tgelafr-pfzr"),
    "timtreis": ("Tim Treis", "https://github.com/timtreis"),
    "tjburns08": ("Tyler Burns", "https://github.com/tjburns08"),
    "yanay-rosen": ("Yanay Rosen", "https://twitter.com/YanayRosen"),
    "yanwu2014": ("Yan Wu", "https://github.com/yanwu2014"),
    "Zethson": ("Lukas Heumos", "https://github.com/Zethson"),
    "zimea": ("Lea Zimmermann", "https://github.com/zimea"),
}
lndocs.authors = authors

blog_baseurl = "https://blog.lamin.ai"
blog_post_pattern = "*"
blog_authors = authors.copy()
blog_authors.update({f"{k}*": v for k, v in authors.items()})
post_date_format = "%Y-%m-%d"
blog_path = "index"
