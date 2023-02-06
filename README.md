# yuque-to-markdown

> status: working in progress

Simple convertor, it converts `.lakebook` to markdown files.

## How to install

```bash
# Make sure your Python3 is installed
python3 -V

# Clone this repo
git clone git@github.com:alswl/yuque2markdown.git
cd yuque2markdown

# Install packages
pip3 install -r requirements.txt
```


## How to convert

1. Go to your yuque book configuration page, click `设置` button
2. Click `导出` button, and download the `.lakebook` file
3. Using this tool to convert it to markdown files

```bash
python3 yuque2markdown.py -i /path/to/your/lakebook/file -o /path/to/your/output/folder
```


## TODO

1. [ ] Convert HTML to markdown
2. [ ] Fetch images
