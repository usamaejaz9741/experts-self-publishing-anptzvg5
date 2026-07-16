"""Per-page inventory paragraph index maps for HTML slot alignment.

Indices refer to raw ``paragraphs`` arrays in content/inventory.json (0-based).
Use the string ``"overflow"`` in content_rows for the remainder of content_intro
after the first sentence is placed in the content-box intro paragraph.
"""

PAGE_SLOTS: dict[str, dict] = {
    "author-website.html": {
        "hero": [1, 2, 3],
        "content_heading": 4,
        "content_intro": 5,
        "content_rows": ["overflow", 6],
        "cta": [7, 8, 9],
        "make_title": 10,
        "make_body": [11, 12, 13, 14, 15],
    },
    "pr-and-publicity.html": {
        "hero": [1, 2, 3],
        "content_heading_split": [4, 5],
        "content_intro": 6,
        "content_rows": ["overflow", 7, 8, 9],
        "cta": [10, 11, 12],
        "make_title": 13,
        "make_body": [14, 15, 16, 17],
    },
    "book-editing-proofreading.html": {
        "hero": [1, 2, 3],
        "content_heading_split": [4, 5],
        "content_intro": 6,
        "content_rows": ["overflow", 7, 8, 9],
        "cta": [10, 11, 12],
        "make_title": 13,
        "make_body": [14, 15, 16],
    },
    "book-cover-design.html": {
        "hero": [1, 2, 3],
        "content_heading_split": [4, 5],
        "content_intro": 6,
        "content_rows": ["overflow", 7, 8, 9, 10],
        "cta": [11, 12, 13],
        "make_title": 14,
        "make_body": [15, 16, 17, 18, 19],
    },
    "ghostwriting.html": {
        "hero": [1, 2, 3],
        "content_heading_empty": True,
        "content_intro": 4,
        "content_rows": ["overflow", 5, 6, 7],
        "cta": [8, 9, 10],
        "make_title": 11,
        "make_body": [12, 13, 14, 15],
    },
    "book-illustration.html": {
        "hero": [1, 2, 3],
        "content_heading_split": [4, 5],
        "content_intro": 6,
        "content_rows": ["overflow", 7, 8, 9],
        "cta": [10, 11, 12],
        "make_title": 13,
        "make_body": [14, 15, 16, 17],
    },
    "book-video-trailers.html": {
        "hero": [1, 2, 3],
        "content_heading_empty": True,
        "content_intro": 4,
        "content_rows": [5, 6, 7],
        "cta_no_doc": True,
        "make_title": 8,
        "make_body": [9, 10, 11, 12],
    },
    "creative-writing.html": {
        "hero": [1, 2, 3],
        "content_heading_empty": True,
        "content_intro": 4,
        "content_rows": ["overflow", 5, 6, 7, 8],
        "cta_no_doc": True,
        "make_title": 9,
        "make_body": [10, 11, 12, 13],
    },
    "children-book-illustration.html": {
        "hero": [0, 1, 2],
        "content_heading_empty": True,
        "content_intro": 3,
        "content_rows": ["overflow", 4],
        "cta_no_doc": True,
        "make_title": 5,
        "make_body": [6, 7],
    },
    "screenplay-script-writing.html": {
        "hero": [0, 1, 2],
        "content_heading_empty": True,
        "content_intro": 2,
        "content_rows": [3, 4],
        "cta_no_doc": True,
        "make_title": 5,
        "make_body": [6, 7],
    },
    "book-marketing.html": {
        "type": "book_marketing",
    },
    "book-publishing.html": {
        "type": "book_publishing",
        "cta_h3_fixed": "Your Next Chapter Starts Here",
        "banner": [1, 2],
        "s1_heading": 3,
        "s1_body": [4, 5, 6],
        "cta": [7, 8],
        "kdp": {
            "heading": 9,
            "intro": [10, 11],
            "bullets": [12, 13, 14, 15],
            "closing": [16, 17],
        },
        "self_kdp": {
            "heading": 18,
            "intro": 19,
            "benefits": [(20, 21), (22, 23), (24, 25), (26, 27), (28, 29)],
        },
        "publish_1": {"heading": 32, "body": [33, 34]},
        "testi": [35, 36, 37],
    },
    "index.html": {
        "type": "index",
        "hero": [1, 2, 3],
        "publish_sec": {"heading": 5, "body": [6, 7]},
        "connect": {"fixed_h3": "Your Trusted", "fixed_h2": "Self-Publishing Experts", "body": [17, 18]},
        "why_choose": {"heading": [19, 20], "intro": [21, 22], "boxes": [(23, 24), (25, 26), (27, 28), (29, 30)]},
        "testi_intro": 14,
    },
    "pricing.html": {
        "type": "pricing",
        "banner": [1, 2, 3],
        "cta_no_doc": True,
    },
    "about-us.html": {
        "banner_fixed_label": "Our Journey",
        "banner": [0, 1],
        "about_heading": 2,
        "about_intro": 3,
        "about_rows": [4, 5, 6],
        "cta": [7, 8, 9],
    },
    "published-books.html": {
        "banner": [1, 2, 3],
    },
    "customer-reviews.html": {
        "banner": [1, 2, 3],
        "books_heading": 4,
        "books_intro": 5,
    },
    "faq.html": {
        "type": "faq",
        "banner_fixed_label": "Our Journey",
    },
}

# Phrases from original UBP template that should not appear outside known gaps.
OLD_PHRASES = [
    "Reach from Simple Draft to Published Success",
    "Let Your Words Find Their Readers",
    "Let Your Words Reach the World",
    "Connect with us today and turn uncertainty",
    "Talk with our experts and get the guidance you need to convert your raw manuscript",
    "United Book Publishing",
    "Struggling With Amazon KDP?",
]

# Pages where old CTA copy is expected until doc provides replacement copy.
CTA_NO_DOC_PAGES = {"pricing.html", "book-video-trailers.html", "creative-writing.html",
                    "children-book-illustration.html", "screenplay-script-writing.html"}
