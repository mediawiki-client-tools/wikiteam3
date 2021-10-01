import delay
import re
import sys
import urllib

from clean_html import cleanHTML, undoHTMLEntities
from domain import domain2prefix
from get_json import getJSON
from handle_status_code import handleStatusCode
from image_url import curateImageURL


def getImageNames(config={}, session=None):
    """Get list of image names"""

    print(")Retrieving image filenames")
    images = []
    if "api" in config and config["api"]:
        images = getImageNamesAPI(config=config, session=session)
    elif "index" in config and config["index"]:
        images = getImageNamesScraper(config=config, session=session)

    # images = list(set(images)) # it is a list of lists
    images.sort()

    print("%d image names loaded" % (len(images)))
    return images


def getImageNamesScraper(config={}, session=None):
    """Retrieve file list: filename, url, uploader"""

    # (?<! http://docs.python.org/library/re.html
    r_next = r"(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;"
    images = []
    offset = "29990101000000"  # january 1, 2999
    limit = 5000
    retries = config["retries"]
    while offset:
        # 5000 overload some servers, but it is needed for sites like this with
        # no next links
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        r = session.post(
            url=config["index"],
            params={"title": "Special:Imagelist", "limit": limit, "offset": offset},
            timeout=30,
        )
        raw = r.text
        delay(config=config, session=session)
        # delicate wiki
        if re.search(
            r"(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)",
            raw,
        ):
            if limit > 10:
                print(
                    "Error: listing %d images in a chunk is not possible, trying tiny chunks"
                    % (limit)
                )
                limit = limit / 10
                continue
            elif retries > 0:  # waste retries, then exit
                retries -= 1
                print("Retrying...")
                continue
            else:
                print("No more retries, exit...")
                break

        raw = cleanHTML(raw)
        # archiveteam 1.15.1 <td class="TablePager_col_img_name"><a href="/index.php?title=File:Yahoovideo.jpg" title="File:Yahoovideo.jpg">Yahoovideo.jpg</a> (<a href="/images/2/2b/Yahoovideo.jpg">file</a>)</td>
        # wikanda 1.15.5 <td class="TablePager_col_img_user_text"><a
        # href="/w/index.php?title=Usuario:Fernandocg&amp;action=edit&amp;redlink=1"
        # class="new" title="Usuario:Fernandocg (página no
        # existe)">Fernandocg</a></td>
        r_images1 = r'(?im)<td class="TablePager_col_img_name"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a>[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # wikijuegos 1.9.5
        # http://softwarelibre.uca.es/wikijuegos/Especial:Imagelist old
        # mediawiki version
        r_images2 = r'(?im)<td class="TablePager_col_links"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a></td>\s*<td class="TablePager_col_img_timestamp">[^<]+</td>\s*<td class="TablePager_col_img_name">[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # gentoowiki 1.18
        r_images3 = r'(?im)<td class="TablePager_col_img_name"><a[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+</td><td class="TablePager_col_thumb"><a[^>]+><img[^>]+></a></td><td class="TablePager_col_img_size">[^<]+</td><td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        # (<a href="/en/Image:109_0923.JPG" title="Image:109 0923.JPG">desc</a>) <a href="/en/upload/c/cd/109_0923.JPG">109 0923.JPG</a> . . 885,713 bytes . . <a href="/en/User:Bfalconer" title="User:Bfalconer">Bfalconer</a> . . 18:44, 17 November 2005<br />
        r_images4 = '(?im)<a href=[^>]+ title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+<a[^>]+>(?P<uploader>[^<]+)</a>'
        r_images5 = (
            r'(?im)<td class="TablePager_col_img_name">\s*<a href[^>]*?>(?P<filename>[^>]+)</a>\s*\(<a href="(?P<url>[^>]+)">[^<]*?</a>\s*\)\s*</td>\s*'
            r'<td class="TablePager_col_thumb">[^\n\r]*?</td>\s*'
            r'<td class="TablePager_col_img_size">[^<]*?</td>\s*'
            r'<td class="TablePager_col_img_user_text">\s*(<a href="[^>]*?" title="[^>]*?">)?(?P<uploader>[^<]+?)(</a>)?\s*</td>'
        )

        # Select the regexp that returns more results
        regexps = [r_images1, r_images2, r_images3, r_images4, r_images5]
        count = 0
        i = 0
        regexp_best = 0
        for regexp in regexps:
            if len(re.findall(regexp, raw)) > count:
                count = len(re.findall(regexp, raw))
                regexp_best = i
            i += 1
        m = re.compile(regexps[regexp_best]).finditer(raw)

        # Iter the image results
        for i in m:
            url = i.group("url")
            url = curateImageURL(config=config, url=url)
            filename = re.sub("_", " ", i.group("filename"))
            filename = undoHTMLEntities(text=filename)
            filename = urllib.parse.unquote(filename)
            uploader = re.sub("_", " ", i.group("uploader"))
            uploader = undoHTMLEntities(text=uploader)
            uploader = urllib.parse.unquote(uploader)
            images.append([filename, url, uploader])
            # print (filename, url)

        if re.search(r_next, raw):
            new_offset = re.findall(r_next, raw)[0]
            # Avoid infinite loop
            if new_offset != offset:
                offset = new_offset
                retries += 5  # add more retries if we got a page with offset
            else:
                offset = ""
        else:
            offset = ""

    if len(images) == 1:
        print("    Found 1 image")
    else:
        print("    Found %d images" % (len(images)))

    images.sort()
    return images


def getImageNamesAPI(config={}, session=None):
    """Retrieve file list: filename, url, uploader"""
    oldAPI = False
    aifrom = "!"
    images = []
    while aifrom:
        sys.stderr.write(".")  # progress
        params = {
            "action": "query",
            "list": "allimages",
            "aiprop": "url|user",
            "aifrom": aifrom,
            "format": "json",
            "ailimit": 50,
        }
        # FIXME Handle HTTP Errors HERE
        r = session.get(url=config["api"], params=params, timeout=30)
        handleStatusCode(r)
        jsonimages = getJSON(r)
        delay(config=config, session=session)

        if "query" in jsonimages:
            aifrom = ""
            if (
                "query-continue" in jsonimages
                and "allimages" in jsonimages["query-continue"]
            ):
                if "aicontinue" in jsonimages["query-continue"]["allimages"]:
                    aifrom = jsonimages["query-continue"]["allimages"]["aicontinue"]
                elif "aifrom" in jsonimages["query-continue"]["allimages"]:
                    aifrom = jsonimages["query-continue"]["allimages"]["aifrom"]
            elif "continue" in jsonimages:
                if "aicontinue" in jsonimages["continue"]:
                    aifrom = jsonimages["continue"]["aicontinue"]
                elif "aifrom" in jsonimages["continue"]:
                    aifrom = jsonimages["continue"]["aifrom"]
            # print (aifrom)

            for image in jsonimages["query"]["allimages"]:
                url = image["url"]
                url = curateImageURL(config=config, url=url)
                # encoding to ascii is needed to work around this horrible bug:
                # http://bugs.python.org/issue8136
                # (ascii encoding removed because of the following)
                #
                # unquote() no longer supports bytes-like strings
                # so unicode may require the following workaround:
                # https://izziswift.com/how-to-unquote-a-urlencoded-unicode-string-in-python/
                if "api" in config and (
                    ".wikia." in config["api"] or ".fandom.com" in config["api"]
                ):
                    filename = urllib.parse.unquote(
                        re.sub("_", " ", url.split("/")[-3])
                    )
                else:
                    filename = urllib.parse.unquote(
                        re.sub("_", " ", url.split("/")[-1])
                    )
                if u"%u" in filename:
                    raise NotImplementedError(
                        "Filename "
                        + filename
                        + " contains unicode. Please file an issue with WikiTeam."
                    )
                uploader = re.sub("_", " ", image["user"])
                images.append([filename, url, uploader])
        else:
            oldAPI = True
            break

    if oldAPI:
        gapfrom = "!"
        images = []
        while gapfrom:
            sys.stderr.write(".")  # progress
            # Some old APIs doesn't have allimages query
            # In this case use allpages (in nm=6) as generator for imageinfo
            # Example:
            # http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6
            # &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
            params = {
                "action": "query",
                "generator": "allpages",
                "gapnamespace": 6,
                "gaplimit": 50,
                "gapfrom": gapfrom,
                "prop": "imageinfo",
                "iiprop": "user|url",
                "format": "json",
            }
            # FIXME Handle HTTP Errors HERE
            r = session.get(url=config["api"], params=params, timeout=30)
            handleStatusCode(r)
            jsonimages = getJSON(r)
            delay(config=config, session=session)

            if "query" in jsonimages:
                gapfrom = ""
                if (
                    "query-continue" in jsonimages
                    and "allpages" in jsonimages["query-continue"]
                ):
                    if "gapfrom" in jsonimages["query-continue"]["allpages"]:
                        gapfrom = jsonimages["query-continue"]["allpages"]["gapfrom"]
                # print (gapfrom)
                # print (jsonimages['query'])

                for image, props in jsonimages["query"]["pages"].items():
                    url = props["imageinfo"][0]["url"]
                    url = curateImageURL(config=config, url=url)

                    tmp_filename = ":".join(props["title"].split(":")[1:])

                    filename = re.sub("_", " ", tmp_filename)
                    uploader = re.sub("_", " ", props["imageinfo"][0]["user"])
                    images.append([filename, url, uploader])
            else:
                # if the API doesn't return query data, then we're done
                break

    if len(images) == 1:
        print("    Found 1 image")
    else:
        print("    Found %d images" % (len(images)))

    return images


def saveImageNames(config={}, images=[], session=None):
    """Save image list in a file, including filename, url and uploader"""

    imagesfilename = "%s-%s-images.txt" % (domain2prefix(config=config), config["date"])
    imagesfile = open("%s/%s" % (config["path"], imagesfilename), "w")
    imagesfile.write(
        (
            "\n".join(
                [
                    filename + "\t" + url + "\t" + uploader
                    for filename, url, uploader in images
                ]
            )
        )
    )
    imagesfile.write("\n--END--")
    imagesfile.close()

    print("Image filenames and URLs saved at...", imagesfilename)
