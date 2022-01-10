# A small script to automatically generate list of tests for the readme file in graph_test_set

# Opens readme file
# Opens and reads each test file
# reads lines
# append relevant lines to readme file
# stops writing when it gets to a cypher query or the actual test.

from datetime import datetime
import glob
import re


def read_template(template_path: str = ".readme/TESTS_README.template") -> str:
    """
    Read a template given a path. Defaults to the TESTS_README template.
    :param template_path: Path to the template
    :returns template: string representation of the content
    """
    with open(template_path, 'r') as f:
        template = f.read()
    return template


def create_index(test_folder: str = "graph_test_set", wildcard= "*.adoc", recursive: bool = False) -> str:
    """
    Create automatic index of the tests inside test_folder. Recursivity is turned off by default.
    :param test_folder: Folder where the tests are located
    :param wildcard: Wildcard to look for the extension of the documents (e.g. *.adoc)
    :param recursive: boolean indicating if recursivity is expected. If recursive is true, please use proper wildcard
    :returns buffer: Content of the index part of the readme
    """
    buffer = ""
    for test in glob.iglob(f"{test_folder}/{wildcard}", recursive=recursive):
        with open(test, "r") as test_file:
            for line in test_file.readlines():
                if re.search("#### The test", line):
                    break
                elif re.search("^----", line):
                    break
                elif line == "\n":
                    continue
                else:
                    if re.search("^## Test: ", line):
                        line = "##" + line[8:]
                    buffer += line
            buffer += "\n"
    return buffer


def main():
    template = read_template()
    index = create_index()

    new_template = template.replace('{{TESTS_INDEX}}', index).replace('{{LAST_UPDATED}}', str(datetime.now().date()))
    with open("graph_test_set/README.md", "w") as readme:
        readme.write(new_template)


if __name__ == '__main__':
    main()
