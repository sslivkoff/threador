
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
# example_raw_thread.txt

this is the first tweet

it is an introduction



this is the next tweet



tweets are separated by 2 or more blank lines



this is the final tweet
```


```bash
> threador raw_thread.txt --index

```



