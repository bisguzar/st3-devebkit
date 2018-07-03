import sublime_plugin
import textwrap
import sublime
import json
import uuid
import re


def plugin_loaded():

    data = json.loads(
        sublime.load_resource(sublime.find_resources("deveb-completions*")[0])
    )

    list_of_attributes = [i for i in data["attributes"]]
    DevebAutoComplations.class_completions = [
        ("%s \tdeveb class" % s, s) for s in data["classes"]
    ]
    DevebAutoComplations.data_completions = [
        ("%s \t deveb attribute" % s, '%s="$1"' % s) for s in data["attributes"]
    ]

    DevebSchemeCommand.schemes = json.loads(
        sublime.load_resource(sublime.find_resources("deveb-schemes*")[0])
    )


class DevebAutoComplations(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):

        if view.match_selector(locations[0], "text.html string.quoted"):

            # Cursor is inside a quoted attribute
            # Now check if we are inside the class attribute

            # max search size
            LIMIT = 250

            # place search cursor one word back
            cursor = locations[0] - len(prefix) - 1

            # dont start with negative value
            start = max(0, cursor - LIMIT - len(prefix))

            # get part of buffer
            line = view.substr(sublime.Region(start, cursor))

            # split attributes
            parts = line.split(" ")

            # is the last typed attribute a class attribute?
            if len(parts) > 1:
                if parts[-1].replace("=", "") in self.list_of_attributes:
                    return self.class_completions
                else:
                    return []
            else:
                return []
        elif view.match_selector(
            locations[0],
            "text.html meta.tag - text.html punctuation.definition.tag.begin",
        ):

            # Cursor is in a tag, but not inside an attribute, i.e. <div {here}>
            # This one is easy, just return completions for the data-uk-* attributes
            return self.data_completions

        else:

            return []


class DevebSchemeCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super().__init__(view)
        self.index = -1

    def run(self, edit):
        point = self.view.sel()[0].b
        line = self.view.substr(self.view.line(point))
        word = line.split()[-1]

        if re.match("^.*de?ve?b\.(sekme|tab)(\d*)$", word):
            count = re.match("^.*(sekme|tab)(.*)$", word).group(2)

            text = self.create_tabs(int(count) if count != "" else 1)

            self.view.replace(
                edit,
                sublime.Region(
                    point, point - len(re.match("^.*de?ve?b\.(sekme|tab)\d*$", word).group())
                ),
                "",
            )
            self.view.run_command("insert_snippet", {"contents": text})

        elif re.match("^.*de?ve?b\.(\d*r)\.?(\d*)?$", word):
            key = re.match("^.*de?ve?b\.(\d*r)\.?(\d*)?$", word).group(1)

            try:
                count = int(re.match("^.*de?ve?b\.(\d*r)\.?(\d*)?$", word).group(2))
            except:
                count = 3

            text = self.dizem_layout(key, count)

            self.view.replace(
                edit,
                sublime.Region(
                    point,
                    point - len(re.match("^.*de?ve?b\.(\d*r)\.?(\d*)?$", word).group()),
                ),
                "",
            )
            self.view.run_command("insert_snippet", {"contents": text})

        elif re.match("^.*de?ve?b\.(\d-(?:\d-)*(?:\d*)?)(\.[a-z]*)?$", word):
            reg_text = re.match("^.*de?ve?b\.(\d-(?:\d-)*(?:\d*)?)(\.[a-z]*)?$", word)
            pieces = reg_text.group(1)
            tag = reg_text.group(2)

            text = self.piece_layout(pieces, tag)

            self.view.replace(
                edit,
                sublime.Region(
                    point,
                    point
                    - len(
                        re.match(
                            "^.*de?ve?b\.(\d-(?:\d-)*(?:\d*)?)(\.[a-z]*)?$", word
                        ).group()
                    ),
                ),
                "",
            )
            self.view.run_command("insert_snippet", {"contents": text})

        else:
            print("yok")

    def create_tabs(self, count):
        frame = "\n".join(self.schemes["sekme"]["frame"])
        element = "\n".join(self.schemes["sekme"]["element"])

        prepare_elements = []
        prepared_elements = []

        for number in range(count):
            time_low = uuid.uuid4().time_low
            prepare_elements.append(
                element.format(
                    id=time_low,
                    name="{name}",
                    baslik="${{1:Sekme-{}}}".format(time_low)
                    if number == 0
                    else "Sekme-{}".format(time_low),
                )
            )

        name_id = "sekme-{}".format(uuid.uuid4().time_low)
        for element in prepare_elements:
            prepared_elements.append(element.replace("{name}", name_id))

        text = frame.format(content="\n".join(prepared_elements))
        return text

    def dizem_layout(self, key, count):
        frame = "\n".join(self.schemes["dizem"]["frame"])
        element = self.schemes["dizem"]["element"]

        prepare_elements = []

        for number in range(count):
            prepare_elements.append(
                element[0].format(
                    cursor="${1: Buraya bir şeyler gelecek...}" if number == 0 else ""
                )
            )

        return frame.format(content="\n".join(prepare_elements), key=key)

    def piece_layout(self, pieces, tag):
        element = "\n".join(self.schemes["parça_düzeni"]["element"])
        supported_elements = self.schemes["parça_düzeni"]["supported_elements"]

        pieces = pieces.split("-")
        pieces = [int(piece) for piece in pieces]
        sum_of_pieces = sum(pieces)
        prepare_elements = []

        # Checking variables
        for number in pieces:  # We don't want zeros as piece
            if not number:
                return
        if sum_of_pieces > 24:  # Summary of pieces should less than 24
            return
        if not tag:
            tag = "div"
        else:
            tag = tag.replace(".", "")
            if not tag in supported_elements:
                return

        for number, piece in enumerate(pieces):
            prepare_elements.append(
                element.format(
                    tag=tag,
                    piece=piece,
                    sum=sum_of_pieces,
                    cursor="$0" if not number else "",
                )
            )

        return "\n".join(prepare_elements)
