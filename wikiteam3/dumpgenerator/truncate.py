from hashlib import md5


def truncateFilename(other={}, filename=""):
    """Truncate filenames when downloading images with large filenames"""
    return (
        filename[: other["filenamelimit"]]
        + md5(str(filename)).hexdigest()
        + "."
        + filename.split(".")[-1]
    )
