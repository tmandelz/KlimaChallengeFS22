import os
import argparse
import signal
import sys
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc

from black import format_str, FileMode
from lxml import etree
from pathlib import Path

def signal_handler(sig, frame):
    print('Goodbye!')
    sys.exit(0)

element_str = """
<div class="container" type="button">
    <h1>Some Test Information</h1>
    <div class="row">
        <div class="col">
        </div>
        <div class="col" id="this-is-some-id">
            <p>hello</p>
        </div>
    </div>
    <div>
        <div class="container">
            <div class="row">
                <div class="col-md-12" id="positions"></div>
            </div>
            <div class="row">
                <div class="col-md-4" id="someofcolumna"></div>
                <div class="col-md-4" id="someofcolumnb"></div>
                <div class="col-md-4" id="someofcolumnc"></div>
            </div>
        </div>
    </div>
</div>
"""

param_map = {
    "class": "className"
}

priority_list = ['dcc', 'dbc', 'html']

allowed_attributes = ["children", "class", "fluid", "id", "key", "loading_state", "style", "tag"]


def method_list(item):
    return [attribute for attribute in dir(item) if
            callable(getattr(item, attribute)) and not attribute.startswith('_')]


tag_map = {
    'dbc': method_list(dbc),
    'html': method_list(html),
    'dcc': method_list(dcc),
}


def parse_format(element, d=0):
    tags_found = []
    for tag in priority_list:
        if element.tag.capitalize() in tag_map[tag]:
            tags_found.append((tag, element.tag.capitalize()))

    for item in element.items():
        if item[0] == 'class':
            for tag in priority_list:
                for x in tag_map[tag]:
                    if x.lower() in [*item[1].split('-')]:
                        tags_found.append((tag, x))
                        break
            break

    tags_found.sort(key=lambda x: priority_list.index(x[0]))

    tag = ".".join(tags_found[0])

    args = []

    attribute_args = [f'{param_map.get(x[0], x[0])}="{x[1]}"' for x in element.items() if x[0] in allowed_attributes]

    if element.text is not None:
        text = element.text.replace('\n', '').strip()
        if text != '':
            args.append('"{}"'.format(text))

    children = element.getchildren()

    if len(children):
        parsed_children = [parse_format(x, d + 1) for x in children if x is not None]
        if len(parsed_children):
            args.extend(parsed_children)

    if len(attribute_args):
        return '{}({},children=[{}])'.format(tag, ",\n".join(attribute_args), ",\n".join(args))
    return '{}(children=[{}])'.format(tag, ",\n".join(args))


def main():
    global element_str
    global priority_list
    parser = argparse.ArgumentParser(description='Convert HTML into Python Code for Dash with bootstrap')
    parser.add_argument('-f', action="store", dest="fil", default=None, help="input file")
    parser.add_argument('-o', action='store', dest="outfile", default=None, help="output file")
    parser.add_argument('-i', action='store_true', help="Interactive mode. (ctrl-c, ctrl-v, then add a terminating character. windows: ctrl-z, linux: ctrl-d.")
    parser.add_argument('-p', action="append", dest="priority_list", default=[],
                        help="priority list for replacing tags."
                             " :: Options: dcc = dash_core_components, dbc = dash_bootstrap_components, html = dash_html_components"
                             " :: Exanple: -p dbc -p html -p dcc"
                             " :: Default Order: dcc, dbc, html")

    results = parser.parse_args()

    if len(results.priority_list):
        priority_list = results.priority_list

    if results.i:
        signal.signal(signal.SIGINT, signal_handler)
        while True:
            print("\nPaste your html here: \n")
            text = sys.stdin.read()
            root = etree.fromstring(text)
            output = format_str(parse_format(root), mode=FileMode())
            print(output)

    else:
        if results.infile is not None:
            if os.path.exists(results.infile):
                element_str = Path(results.infile).read_text().replace('\n', '')

        root = etree.fromstring(element_str)
        output = format_str(parse_format(root), mode=FileMode())

        if results.outfile is not None:
            if os.path.isfile(results.outfile):
                overwrite = input('File already exists. Overwrite? Y = yes, N = no\n')
                if overwrite.lower() == 'y':
                    # call the function that writes the file here. use 'w' on the open handle
                    with open(results.outfile, 'w') as f:
                        f.write(output)

        print(output)


if __name__ == '__main__':
    main()



