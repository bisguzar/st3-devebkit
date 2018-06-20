import sublime_plugin
import textwrap
import sublime
import json
import uuid
import re


class DevebAutoComplations(sublime_plugin.EventListener):
    def __init__(self):

        data = json.loads(
            sublime.load_resource(sublime.find_resources("deveb-completions*")[0])
        )

        self.data, data = data, None
        self.list_of_attributes = [i for i in self.data["attributes"]]
        self.class_completions = [
            ("%s \tdeveb class" % s, s) for s in self.data["classes"]
        ]
        self.data_completions = [
            ("%s \t deveb attribute" % s, '%s="$1"' % s)
            for s in self.data["attributes"]
        ]

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
        self.schemes = json.loads(
            sublime.load_resource(sublime.find_resources("deveb-schemes*")[0])
        )

    def run(self, edit):
        # Get the last word of the line the cursor is on, then discard the word
        # "lorem" from the start, leaving the remainder
        point = self.view.sel()[0].b
        line = self.view.substr(self.view.line(point))
        word = line.split()[-1]

        """
        repeats = int(word if word != "" else "1")

        self.view.replace(edit, sublime.Region(point, point - 5 - len(word)), "")


        for _ in range(repeats):
            self.view.run_command("insert", {"characters": self.text()})
            if _ + 1 < repeats:
                self.view.run_command("insert", {"characters": "\n\n"})
        """

        if re.match("^.*de?ve?b\.sekme(\d*)$", word):
            count = re.match("^.*sekme(.*)$", word).group(1)

            text = self.create_tabs(int(count) if count != "" else 1)

            self.view.replace(
                edit,
                sublime.Region(
                    point, point - len(re.match("^.*de?ve?b\.sekme\d*$", word).group())
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

        else:
            print("yok")

    def text(self):
        point = self.view.sel()[0].b
        col = self.view.rowcol(point)[1]
        width = next(iter(self.view.settings().get("rulers", [])), 72) - col

        self.index += 1
        if self.index == len(_paragraphs):
            self.index = 0

        return textwrap.fill(_paragraphs[self.index], 10 if width < 10 else width)

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
