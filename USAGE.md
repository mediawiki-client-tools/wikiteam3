# `MediaWiki Dump Generator Usage`

**MediaWiki Dump Generator can archive wikis from the largest to the tiniest.**

`MediaWiki Dump Generator` is an ongoing project to port the legacy [`wikiteam`](https://github.com/WikiTeam/wikiteam) toolset to Python 3 and PyPI to make it more accessible for today's archivers.

Most of the focus has been on the core `dumpgenerator` tool, but Python 3 versions of the other `wikiteam` tools may be added over time.

## MediaWiki Dump Generator Toolset

MediaWiki Dump Generator is a set of tools for archiving wikis. The main general-purpose module of MediaWiki Dump Generator is dumpgenerator, which can download XML dumps of MediaWiki sites that can then be parsed or redeployed elsewhere.

Wikipedia is far too large to manage the dump easily, [dumps are already freely available](https://en.wikipedia.org/wiki/Wikipedia:Database_download#Where_do_I_get_the_dumps?).

### Viewing MediaWiki XML Dumps

* [XML namespaces](https://www.mediawiki.org/xml/)
* [XML export format](https://www.mediawiki.org/wiki/Help:Export#Export_format)

## Python Environment

`MediaWiki Dump Generator` requires [Python 3.8](https://www.python.org/downloads/release/python-380/) or later (less than 4.0), but you may be able to get it run with earlier versions of Python 3. On recent versions of Linux and macOS Python 3.8 should come preinstalled, but on Windows you will need to install it from [python.org](https://www.python.org/downloads/release/python-380/).

`MediaWiki Dump Generator` has been tested on Linux, macOS, Windows and Android. If you are connecting to Linux or macOS via `ssh`, you can continue using the `bash` or `zsh` command prompt in the same terminal, but if you are starting in a desktop environment and don't already have a preferred Terminal see the INSTALLATION.md document.

After installing `MediaWiki Dump Generator` using `pip` you should be able to use the `dumpgenerator` command from any local directory.

For basic usage, you can run `dumpgenerator` in the directory where you'd like the download to be.

For a brief summary of the `dumpgenerator` command-line options:

```bash
dumpgenerator --help
```

Several examples follow.

> **Note:** the `\` and line breaks in the examples below are for legibility in this documentation. Run `dumpgenerator` with the arguments in a single line and a single space between.

### Downloading a wiki with complete XML history and images

```bash
dumpgenerator http://wiki.domain.org --xml --images
```

### Manually specifying `api.php` and/or `index.php`

If the script itself can't find the `api.php` and/or `index.php` paths, then you can provide them. To find api.php on a particular wiki, see section "Entry point URLs" on the Special:Version page.

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images
```

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --index http://wiki.domain.org/w/index.php \
    --xml --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --curonly`.

To dump a private wiki you will have to use a login which has at the least read permission on that wiki.

### Resuming an incomplete dump

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php --xml --images --resume --path /path/to/incomplete-dump
```

In the above example, `--path` is only necessary if the download path is not the default.

`dumpgenerator` will also ask you if you want to resume if it finds an incomplete dump in the path where it is downloading.

## Checking dump integrity

If you want to check the XML dump integrity, type this into your command line to count title, page and revision XML tags:

```bash
grep -Ec "<title(.*?)>" *.xml;grep -Ec "<page(.*?)>" *.xml;grep -Ec "</page>" *.xml; \
    grep -Ec "<revision(.*?)>" *.xml;grep -Ec "</revision>" *.xml
```

You should see something similar to this (not the actual numbers) - the first three numbers should be the same and the last two should be the same as each other:

```bash
580
580
580
5677
5677
```

If your first three numbers or your last two numbers are different, then, your XML dump is corrupt (it contains one or more unfinished ```</page>``` or ```</revision>```). This is not common in small wikis, but large or very large wikis may fail at this due to truncated XML pages while exporting and merging. The solution is to remove the XML dump and re-download, a bit boring, and it can fail again.

## Publishing the dump

Please consider publishing your wiki dump(s). You can do it yourself as explained at WikiTeam's [Publishing the dump](https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump) tutorial.

## Using `launcher`

`launcher` is a way to download a list of wikis with a single invocation.

Usage:

```bash
launcher path-to-apis.txt [--7z-path path-to-7z] [--generator-arg=--arg] ...
```

`launcher` will download a complete dump (XML and images) for a list of wikis, then compress the dump into two `7z` files: `history` (containing only metadata and the XML history of the wiki) and `wikidump` (containing metadata, XML, and images). This is the format that is suitable for upload to a WikiTeam item on the Internet Archive.

`launcher` will resume incomplete dumps as appropriate and will not attempt to download wikis that have already been downloaded (as determined by the files existing in the working directory).

Each wiki will be stored into files contiaining a stripped version of the url and the date the dump was started.

`path-to-apis.txt` is a path to a file that contains a list of URLs to `api.php`s of wikis, one on each line.

By default, a `7z` executable is found on `PATH`. The `--7z-path` argument can be used to use a specific executable instead.

The `--generator-arg` argument can be used to pass through arguments to the `generator` instances that are spawned. For example, one can use `--generator-arg=--xmlrevisions` to use the modern MediaWiki API for retrieving revisions or `--generator-arg=--delay=2` to use a delay of 2 seconds between requests.

## Using `uploader`

`uploader` is a way to upload a set of already-generated wiki dumps to the Internet Archive with a single invocation.

Usage:

```bash
uploader [-pd] [-pw] [-a] [-c COLLECTION] [-wd WIKIDUMP_DIR] [-u] [-kf KEYSFILE] [-lf LOGFILE] listfile
```

For the positional parameter `listfile`, `uploader` expects a path to a file that contains a list of URLs to `api.php`s of wikis, one on each line (exactly the same as `launcher`).

`uploader` will search a configurable directory for files with the names generated by `launcher` and upload any that it finds to an Internet Archive item. The item will be created if it does not already exist.

Named arguments (short and long versions):

* `-pd`, `--prune_directories`: After uploading, remove the raw directory generated by `launcher`
* `-pw`, `--prune_wikidump`: After uploading, remove the `wikidump.7z` file generated by `launcher`
* `-c`, `--collection`: Assign the Internet Archive items to the specified collection
* `-a`, `--admin`: Used only if you are an admin of the WikiTeam collection on the Internet Archive
* `-wd`, `--wikidump_dir`: The directory to search for dumps. Defaults to `.`.
* `-u`, `--update`: Update the metadata on an existing Internet Archive item
* `-kf`, `--keysfile`: Path to a file containing Internet Archive API keys. Should contain two lines: the access key, then the secret key. Defaults to `./keys.txt`.
* `-lf`, `--logfile`: Where to store a log of uploaded files (to reduce duplicate work). Defaults to `uploader-X.txt`, where `X` is the final part of the `listfile` path.

## Restoring a wiki

To restore a wiki from a wikidump follow the instructions at MediaWiki's [Manual:Restoring a wiki from backup](https://www.mediawiki.org/wiki/Manual:Restoring_a_wiki_from_backup).

## Getting help

* You can read and post in MediaWiki Client Tools' [GitHub Discussions]( https://github.com/orgs/mediawiki-client-tools/discussions).
* If you need help (other than reporting a bug), you can reach out on MediaWiki Client Tools' [Discussions/Q&A](https://github.com/orgs/mediawiki-client-tools/discussions/categories/q-a).

## Contributing

For information on reporting bugs and proposing changes, please see the [Contributing](./Contributing.md) guide.

## Code of Conduct

`mediawiki-client-tools` has a [Code of Conduct](./CODE_OF_CONDUCT.md).

At the moment the only person responsible for reviewing CoC reports is the repository administrator, Elsie Hupp, but we will work towards implementing a broader-based approach to reviews.

You can contact Elsie Hupp directly via email at [mediawiki-client-tools@elsiehupp.com](mailto:mediawiki-client-tools@elsiehupp.com) or on Matrix at [@elsiehupp:beeper.com](https://matrix.to/#/@elsiehupp:beeper.com). (Please state up front if your message concerns the Code of Conduct, as these messages are confidential.)

## Contributors

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) [[GitHub](https://github.com/ArchiveTeam)] subcommittee on wikis.
It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Thanks to people who have helped, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

**MediaWiki Dump Generator**
The Python 3 initiative is currently being led by [Elsie Hupp](https://github.com/elsiehupp), with contributions from [Victor Gambier](https://github.com/vgambier), [Thomas Karcher](https://github.com/t-karcher), [Janet Cobb](https://github.com/randomnetcat), [yzqzss](https://github.com/yzqzss), [NyaMisty](https://github.com/NyaMisty) and [Rob Kam](https://github.com/robkam)