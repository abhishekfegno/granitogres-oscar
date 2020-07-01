from elasticsearch_dsl import analyzer, tokenizer, normalizer

title_ngram_analyzer = analyzer(
    "title_ngram_analyzer",
    tokenizer=tokenizer("trigram", "nGram", min_gram=3, max_gram=7),
    filter=[
        'standard',
        'lowercase',
        'stop',
        'snowball',
    ]
)

lowercase = normalizer('my_analyzer',
                       filter=['lowercase']
                       )

html_strip = analyzer(
    'html_strip',
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)





