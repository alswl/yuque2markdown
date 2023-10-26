# coding=utf-8
import json
import os
import random
import shutil
import sys
import argparse
import tarfile
from markdownify import markdownify as md
from bs4 import BeautifulSoup
from requests import get

import yaml


TYPE_TITLE = "TITLE"
TYPE_DOC = "DOC"
META_JSON = "$meta.json"
TMP_DIR = "/tmp"

DEFAULT_HEADING_STYLE = "ATX"

content_type_to_extension = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
    "image/png": ".png",
}


def sanitizer_file_name(name):
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace(" ", "_")
    name = name.replace("?", "_")
    name = name.replace("*", "_")
    name = name.replace("<", "_")
    name = name.replace(">", "_")
    name = name.replace("|", "_")
    name = name.replace('"', "_")
    name = name.replace(":", "_")
    return name


def read_toc(random_tmp_dir):
    # open meta json
    f = open(os.path.join(random_tmp_dir, META_JSON), "r")
    meta_file_str = json.loads(f.read())
    meta_str = meta_file_str.get("meta", "")
    meta = json.loads(meta_str)
    toc_str = meta.get("book", {}).get("tocYml", "")
    toc = yaml.unsafe_load(toc_str)
    f.close()
    return toc


def extract_repos(repo_dir, output, toc, download_image):
    last_level = 0
    last_sanitized_title = ""
    path_prefixed = []
    for item in toc:
        t = item["type"]
        url = str(item.get("url", ""))
        current_level = item.get("level", 0)
        title = str(item.get("title", ""))
        sanitized_title = sanitizer_file_name(str(title))
        if not title:
            continue
        while True:
            if os.path.exists(os.path.join(output, sanitized_title)):
                sanitized_title = sanitizer_file_name(str(title)) + str(
                    random.randint(0, 1000)
                )
            break

        if current_level > last_level:
            path_prefixed = path_prefixed + [last_sanitized_title]
        elif current_level < last_level:
            diff = last_level - current_level
            path_prefixed = path_prefixed[0:-diff]

        # else:
        if t == TYPE_DOC:
            output_dir_path = os.path.join(output, *path_prefixed)
            if not os.path.exists(output_dir_path):
                os.makedirs(output_dir_path)
            raw_path = os.path.join(repo_dir, url + ".json")
            raw_file = open(raw_path, "r")
            doc_str = json.loads(raw_file.read())
            html = doc_str["doc"]["body"] or doc_str["doc"]["body_asl"]

            if download_image:
                html = download_images_and_patch_html(
                    output_dir_path, sanitized_title, html
                )

            output_path = os.path.join(output_dir_path, sanitized_title + ".md")
            f = open(output_path, "w")
            f.write(pretty_md(md(html, heading_style=DEFAULT_HEADING_STYLE)))

        last_sanitized_title = sanitized_title
        last_level = current_level


def download_images_and_patch_html(output_dir_path, sanitized_title, html):
    bs = BeautifulSoup(html, "html.parser")
    if len(bs.find_all("img")) > 0:
        attachments_dir_path = os.path.join(output_dir_path, "attachments")
        if not os.path.exists(attachments_dir_path):
            os.mkdir(attachments_dir_path)
        no = 1
        for image in bs.find_all("img"):
            print("Download %s" % image["src"])
            resp = get(image["src"])
            file_name = sanitized_title + "_%03d%s" % (
                no,
                content_type_to_extension.get(resp.headers["Content-Type"], ""),
            )
            attachments_file_path = os.path.join(attachments_dir_path, file_name)
            with open(attachments_file_path, "wb") as f:
                f.write(resp.content)
            no = no + 1
            image["src"] = "./attachments/" + file_name
        html = str(bs)
        return html
    else:
        return html


def pretty_md(text: str) -> str:
    output = text

    lines = output.split("\n")
    for i in range(len(lines)):
        lines[i] = lines[i].rstrip()
    output = "\n".join(lines)

    for i in range(50):
        output = output.replace("\n\n\n", "\n\n")
        if "\n\n\n" not in output:
            break

    return output


def main():
    parser = argparse.ArgumentParser(description="Convert Yuque doc to markdown")
    parser.add_argument("lakebook", help="Lakebook file")
    parser.add_argument("output", help="Output directory")
    parser.add_argument(
        "--download-image", help="Download images to local", action="store_true"
    )
    args = parser.parse_args()
    if not os.path.exists(args.lakebook):
        print("Lakebook file not found: " + args.lakebook)
        sys.exit(1)
    if not os.path.exists(args.output):
        os.mkdir(args.output)

    # extract lakebook file
    random_tmp_dir = os.path.join(TMP_DIR, "lakebook_" + str(os.getpid()))
    extract_tar(args.lakebook, random_tmp_dir)
    # detect only one directory in random_tmp_dir
    repo_dir = ""
    for root, dirs, files in os.walk(random_tmp_dir):
        for d in dirs:
            repo_dir = os.path.join(random_tmp_dir, d)
            break
    if not repo_dir:
        print(".lakebook file is invalid")
        sys.exit(1)

    toc = read_toc(repo_dir)
    # print len of toc
    print("Total " + str(len(toc)) + " files")

    extract_repos(repo_dir, args.output, toc, args.download_image)

    # remove tmp dir
    shutil.rmtree(random_tmp_dir)


# extract tar file in tar.gz
def extract_tar(tar_file, target_dir):
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    tar = tarfile.open(tar_file)
    names = tar.getnames()
    for name in names:
        tar.extract(name, target_dir)
    tar.close()


if __name__ == "__main__":
    main()
