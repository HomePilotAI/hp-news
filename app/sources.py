from __future__ import annotations

DEFAULT_SOURCES = [
    {"id":"bbc_world_rss","kind":"rss","name":"BBC World","topic":"world","url":"https://feeds.bbci.co.uk/news/world/rss.xml","weight":1.2,"enabled":1},
    {"id":"bbc_business_rss","kind":"rss","name":"BBC Business","topic":"business","url":"https://feeds.bbci.co.uk/news/business/rss.xml","weight":1.1,"enabled":1},
    {"id":"bbc_sport_rss","kind":"rss","name":"BBC Sport","topic":"sports","url":"https://feeds.bbci.co.uk/sport/rss.xml","weight":0.9,"enabled":1},
    {"id":"verge_rss","kind":"rss","name":"The Verge","topic":"tech","url":"https://www.theverge.com/rss/index.xml","weight":1.0,"enabled":1},
    {"id":"hn_front","kind":"rss","name":"Hacker News Frontpage","topic":"tech","url":"https://hnrss.org/frontpage","weight":1.0,"enabled":1},
    {"id":"variety_rss","kind":"rss","name":"Variety","topic":"entertainment","url":"https://variety.com/feed/","weight":0.9,"enabled":1},
    {"id":"nature_news_rss","kind":"rss","name":"Nature News","topic":"science","url":"https://www.nature.com/subjects/science/rss","weight":1.0,"enabled":1},
]

GOOGLE_NEWS_RSS_QUERIES = [
    {"id":"gn_world","topic":"world","q":"world news"},
    {"id":"gn_business","topic":"business","q":"business news"},
    {"id":"gn_tech","topic":"tech","q":"technology news"},
    {"id":"gn_science","topic":"science","q":"science news"},
    {"id":"gn_sports","topic":"sports","q":"sports news"},
    {"id":"gn_ent","topic":"entertainment","q":"entertainment news"},
]
