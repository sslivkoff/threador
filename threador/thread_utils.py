#!/usr/bin/env python3
"""parse and format twitter threads and show relevant statistics


## Tweet parsing rules
- tweets are delimited by one of:
    - 3 or more newlines in a row
    - a row that contains only horizontal dashes {-, ─}
- annotations are lines of a tweet enclosed by square brackets


## References
- https://developer.twitter.com/en/docs/counting-characters


## TODO
- special implement detailed char counting rules
    - urls
    - mentions
    - emojis
    - generic unicode
"""

from __future__ import annotations

import typing
import argparse

import toolstr

if typing.TYPE_CHECKING:
    import typing_extensions

    class Tweet(typing_extensions.TypedDict):
        text: str
        annotations: TweetAnnotations
        length: int

    class TweetAnnotations(typing_extensions.TypedDict):
        comments: typing.MutableSequence[str]
        images: typing.MutableSequence[str]
        unknown_annotations: typing.MutableSequence[str]
        table_of_contents: bool
        section_start: str | None

    class ScriptArgs(typing_extensions.TypedDict):
        path: str
        add_index: bool
        add_image_hashes: bool
        print_tweets: bool
        print_annotations: bool
        print_summary: bool
        use_color: bool
        oversized_only: bool


char_limit = 280

styles = {
    'chrome': '#999999',
    'tweet': '#8be9fd',
    'compliant': '#b9f29f bold',
    'near_limit': '#f1fa8c bold',
    'violation': '#ff0000 bold',
}


def parse_args() -> ScriptArgs:

    parser = argparse.ArgumentParser(
        description='parse, format, and summarize tweets'
    )

    # add arguments
    parser.add_argument('path', help='path to markdown file')
    parser.add_argument(
        '--index',
        help='add index to end of each tweet',
        action='store_true',
    )
    parser.add_argument(
        '--no-print',
        help='do not print tweets',
        action='store_true',
    )
    parser.add_argument(
        '--no-annotations',
        help='do not print tweet annotations',
        action='store_true',
    )
    parser.add_argument(
        '--no-summary',
        help='do not print a tweet summary',
        action='store_true',
    )
    parser.add_argument(
        '--color',
        help='use colors even when piped to other program',
        action='store_true',
    )
    parser.add_argument(
        '--oversized',
        help='show only tweets that exceed the length limit',
        action='store_true',
    )
    parser.add_argument(
        '--image-hashes',
        help='give a unique hash next to each image (useful for long threads)',
        action='store_true',
    )

    # parse arguments
    args = parser.parse_args()
    return {
        'path': args.path,
        'add_index': args.index,
        'print_tweets': not args.no_print,
        'print_annotations': not args.no_annotations,
        'print_summary': not args.no_summary,
        'use_color': args.color,
        'oversized_only': args.oversized,
        'add_image_hashes': args.image_hashes,
    }


def str_to_tweets(
    content: str,
    add_indices: bool,
    add_image_hashes: bool,
) -> typing.Sequence[Tweet]:
    """see parsing rules above"""

    # remove lines that are purely horizontal dashes
    lines = content.split('\n')
    for i, line in enumerate(list(lines)):
        if len(line) > 0 and set(line).issubset({'-', '─'}):
            lines[i] = '\n\n\n'
    content = '\n'.join(lines)

    # get rid of any set of 4 blank lines or more
    content = content.strip()
    while '\n\n\n\n' in content:
        content = content.replace('\n\n\n\n', '\n\n\n')

    # split into raw tweets
    raw_tweets = content.split('\n\n\n')

    # parse raw tweets
    tweets = []
    add_toc = False
    for t, raw_tweet in enumerate(raw_tweets):

        lines = raw_tweet.split('\n')

        tweet_lines = []
        annotations: TweetAnnotations = {
            'comments': [],
            'images': [],
            'unknown_annotations': [],
            'table_of_contents': False,
            'section_start': None,
        }
        for line in lines:
            if line.startswith('['):
                line = line.lstrip('[').rstrip(']')

                if line == 'table of contents':
                    annotations['table_of_contents'] = True
                    add_toc = True
                    tweet_lines.append('<TOC>')
                elif line.startswith('section: '):
                    annotations['section_start'] = line.split(': ')[1]
                elif line.startswith('image: '):
                    image = line.split(': ')[1]
                    if add_image_hashes:
                        import hashlib

                        image_hash = hashlib.md5(image.encode()).hexdigest()
                        image_hash = image_hash[:10]
                        image = image_hash + ' ' + image
                    annotations['images'].append(image)
                elif line.startswith('comment: '):
                    annotations['comments'].append(line.split(': ')[1])
                else:
                    annotations['unknown_annotations'].append(line)

            else:
                tweet_lines.append(line)

        text = '\n'.join(tweet_lines)
        text = text.strip()

        # TODO: count length more accurately
        length = len(text)

        tweet: Tweet = {
            'text': text,
            'annotations': annotations,
            'length': length,
        }

        tweets.append(tweet)

    if add_toc:

        toc_template = 'table of contents\n{toc_lines}'

        if len(tweets) < 10:
            toc_section_template = 'tweets {start:01} - {end} = {name}'
        elif len(tweets) < 100:
            toc_section_template = 'tweets {start:02} - {end} = {name}'
        else:
            toc_section_template = 'tweets {start:03} - {end} = {name}'

        # gather sections
        sections = []
        for t, tweet in enumerate(tweets):
            section_start = tweet['annotations']['section_start']
            if section_start is not None:
                sections.append({'name': section_start, 'start': t + 1})
        for s, section in enumerate(sections[:-1]):
            sections[s]['end'] = sections[s + 1]['start']
        sections[-1]['end'] = len(tweets)

        # build toc text
        toc_lines = [
            toc_section_template.format(**section) for section in sections
        ]
        toc_text = toc_template.format(toc_lines='\n'.join(toc_lines))

        # add toc to tweets
        for tweet in tweets:
            if tweet['annotations']['table_of_contents']:
                tweet['text'] = tweet['text'].replace('<TOC>', toc_text)

    if add_indices:
        for t, tweet in enumerate(tweets):
            tweet['text'] += '\n\n' + str(t + 1) + ' / ' + str(len(tweets))

    for tweet in tweets:
        tweet['length'] = compute_tweet_length(tweet['text'])

    return tweets


def compute_tweet_length(text: str) -> int:

    # replace urls with 13 character tokens
    tokens = []
    for token in text.split(' '):
        if '.' in token and token[-1] != '.' and '..' not in token:
            token = 'X' * 13
        tokens.append(token)
    text = ' '.join(tokens)

    # TODO: emojis / unicode
    pass

    return len(text)


def print_tweets(
    tweets: typing.Sequence[Tweet],
    print_annotations: bool,
    oversized_only: bool,
) -> None:

    for t, tweet in enumerate(tweets):

        if oversized_only and tweet['length'] <= char_limit:
            continue

        toolstr.print_horizontal_line(style=styles['chrome'])
        if print_annotations:
            section_start = tweet['annotations']['section_start']
            if section_start is not None:
                section_title = toolstr.get_outlined_text(
                    ' NEW SECTION = ' + section_start,
                    style=styles['compliant'],
                    lower_border=True,
                    left_border=True,
                )
                toolstr.print(section_title, justify='right')

        toolstr.print(tweet['text'], style=styles['tweet'])

        if print_annotations:
            annotations = tweet['annotations']
            keys: typing.Sequence[
                typing_extensions.Literal[
                    'comments', 'images', 'unknown_annotations'
                ]
            ] = ['comments', 'images', 'unknown_annotations']
            for key in keys:
                if len(annotations[key]) > 0:
                    print()
                    toolstr.print(key, style=styles['chrome'])
                    for annotation in annotations[key]:
                        toolstr.print('-', annotation, style=styles['chrome'])

        if tweet['length'] > char_limit:
            metadata_style = styles['violation']
        elif char_limit - tweet['length'] < 15:
            metadata_style = styles['near_limit']
        else:
            metadata_style = styles['compliant']

        toolstr.print(
            'length = ' + str(tweet['length']) + ' chars',
            justify='right',
            style=metadata_style,
        )


def print_tweet_summary(tweets: typing.Sequence[Tweet]) -> None:

    big_tweets = [tweet for tweet in tweets if tweet['length'] > char_limit]
    n_over_char_limit = len(big_tweets)

    toolstr.print_text_box('Tweet thread summary')
    print('- number of tweets:', len(tweets))
    print('- number of tweets over char limit:', n_over_char_limit)
    if len(big_tweets) > 0:
        big_tweet_lengths = [str(tweet['length']) for tweet in big_tweets]
        print('    - lengths: ' + ', '.join(big_tweet_lengths))

    images = [
        image for tweet in tweets for image in tweet['annotations']['images']
    ]
    print()
    print('images: ' + str(len(images)))
    for image in images:
        print('- ' + image)

    unknown_annotations = [
        annotation
        for tweet in tweets
        for annotation in tweet['annotations']['unknown_annotations']
    ]
    print()
    print('unknown_annotations: ' + str(len(unknown_annotations)))
    for annotation in unknown_annotations:
        print('-', annotation)


def main() -> None:

    # parse innput args
    args = parse_args()

    # load markdown file
    path = args['path']
    with open(path, 'r') as f:
        content = f.read()

    # process markdown content
    tweets = str_to_tweets(
        content,
        add_indices=args['add_index'],
        add_image_hashes=args['add_image_hashes'],
    )

    # print tweets
    if args['use_color']:
        toolstr.set_default_color_system('truecolor')
    if args['print_tweets']:
        print_tweets(
            tweets,
            print_annotations=args['print_annotations'],
            oversized_only=args['oversized_only'],
        )

        if args['print_summary']:
            toolstr.print_horizontal_line()

    # print tweet summary
    if args['print_summary']:
        print_tweet_summary(tweets)


if __name__ == '__main__':
    main()
