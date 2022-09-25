
# threador

Threador is a cli tool for formatting tweet threads

Features
- tweet length testing
- add indexing numbers to each tweet
- tracking of images needed for each tweet
- table of contents creation


## installation

`pip install pythreador`


## usage

`threador <raw_text_file>`

`threador <raw_text_file> --index`

`threador --color | less -R`


## example

```
this is the first tweet

it is an introduction

-

this is the next tweet
[image: happy_emoji.png]
[image: confused_emoji.png]

-

tweets are separated by either:
- 2 or more blank lines
- a line containing only horizontal dashes (- or ─)

-

this is the final tweet
```

(note that in a terminal this output is colored for better readability)

```bash
> threador raw_thread.txt --index
────────────────────────────────────────────────────────────────────────────────────
this is the first tweet

it is an introduction
                                                                   length = 46 chars
────────────────────────────────────────────────────────────────────────────────────
this is the next tweet

images
- happy_emoji.png
- confused_emoji.png
                                                                   length = 22 chars
────────────────────────────────────────────────────────────────────────────────────
tweets are separated by either:
- 2 or more blank lines
- a line containing only horizontal dashes (- or ─)
                                                                  length = 107 chars
────────────────────────────────────────────────────────────────────────────────────
this is the final tweet
                                                                   length = 23 chars
────────────────────────────────────────────────────────────────────────────────────
┌──────────────────────┐
│ Tweet thread summary │
└──────────────────────┘
- number of tweets: 4
- number of tweets over char limit: 0

images: 2
- happy_emoji.png
- confused_emoji.png

unknown_annotations: 0

```
