#!/usr/bin/env python3
"""parse and format twitter threads and show relevant statistics


## Tweet parsing rules
- tweets are delimited by 3 or more newlines in a row
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
        annotations: typing.Sequence[str]
        length: int

    class ScriptArgs(typing_extensions.TypedDict):
        path: str
        add_index: bool
        print_tweets: bool
        print_annotations: bool
        print_summary: bool


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

    # parse arguments
    args = parser.parse_args()
    return {
        'path': args.path,
        'add_index': args.index,
        'print_tweets': not args.no_print,
        'print_annotations': not args.no_annotations,
        'print_summary': not args.no_summary,
        'use_color': args.color,
    }


def str_to_tweets(content: str, add_indices: bool) -> typing.Sequence[Tweet]:
    """see parsing rules above"""

    # get rid of any set of 4 blank lines or more
    while '\n\n\n\n' in content:
        content = content.replace('\n\n\n\n', '\n\n\n')

    # split into raw tweets
    raw_tweets = content.split('\n\n\n')

    # parse raw tweets
    tweets = []
    for raw_tweet in raw_tweets:

        lines = raw_tweet.split('\n')

        tweet_lines = []
        annotations = []
        for line in lines:
            if line.startswith('['):
                line = line.lstrip('[').rstrip(']')
                annotations.append(line)
            else:
                tweet_lines.append(line)

        text = '\n'.join(tweet_lines)

        # TODO: count length more accurately
        length = len(text)

        tweet: Tweet = {
            'text': text,
            'annotations': annotations,
            'length': length,
        }

        tweets.append(tweet)

    if add_indices:
        for t, tweet in enumerate(tweets):
            tweet['text'] += '\n\n' + str(t + 1) + ' / ' + str(len(tweets))
            tweet['length'] = len(tweet['text'])

    return tweets


def print_tweets(
    tweets: typing.Sequence[Tweet],
    print_annotations: bool,
    use_color: bool,
) -> None:

    if use_color:
        color_system = 'truecolor'
    else:
        color_system = None

    for t, tweet in enumerate(tweets):
        toolstr.print_horizontal_line(style=styles['chrome'])
        toolstr.print(
            tweet['text'], style=styles['tweet'], color_system=color_system
        )

        if print_annotations:
            if len(tweet['annotations']) > 0:
                print()
                toolstr.print(
                    'annotations',
                    style=styles['chrome'],
                    color_system=color_system,
                )
            for annotation in tweet['annotations']:
                toolstr.print(
                    '-',
                    annotation,
                    style=styles['chrome'],
                    color_system=color_system,
                )

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
            color_system=color_system,
        )


def print_tweet_summary(tweets: typing.Sequence[Tweet]) -> None:

    big_tweets = [tweet for tweet in tweets if tweet['length'] > char_limit]
    n_over_char_limit = len(big_tweets)

    toolstr.print_text_box('Tweet thread summary')
    print('- number of tweets:', len(tweets))
    print('- number of tweets over char limit:', n_over_char_limit)

    # annotations
    all_annotations = [
        annotation for tweet in tweets for annotation in tweet['annotations']
    ]
    if len(all_annotations) == 0:
        print('- no annotations')
    else:
        print('- annotations (' + str(len(all_annotations)) + '):')
        for a, annotation in enumerate(all_annotations):
            print('    ' + str(a + 1) + '. ' + annotation)


def main() -> None:

    # parse innput args
    args = parse_args()

    # load markdown file
    path = args['path']
    with open(path, 'r') as f:
        content = f.read()

    # process markdown content
    tweets = str_to_tweets(content, add_indices=args['add_index'])

    # print tweets
    if args['print_tweets']:
        print_tweets(
            tweets,
            print_annotations=args['print_annotations'],
            use_color=args['use_color'],
        )

        if args['print_summary']:
            toolstr.print_horizontal_line()

    # print tweet summary
    if args['print_summary']:
        print_tweet_summary(tweets)


if __name__ == '__main__':
    main()
