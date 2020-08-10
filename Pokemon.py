from datetime import datetime


class Pokemon:
    def __init__(self, info, IVs, _dict):
        self.name = " ".join(info[info.index("This") + 1 : info.index("was")])
        self.date = self.get_date(info[info.index("on") + 1])
        self.location = self.split(self.get_location(info))
        self.code = self.code(self.location, _dict)
        self.IVs = IVs

    def __str__(self):
        return ", ".join(
            [
                self.name,
                str(self.date),
                self.location[0],
                self.code,
                "-".join([str(self.IVs[0]), str(self.IVs[1]), str(self.IVs[2])]),
            ]
        )

    @staticmethod
    def get_date(date_str):
        return datetime.strptime((date_str), "%m/%d/%Y").date()

    @staticmethod
    def split(location):
        split_locations = ["", "", ""]
        index = 0
        for i in location:
            split_locations[index] += i
            if i[-1] == "," or i[-1] == ".":
                split_locations[index] = split_locations[index][:-1]
                index += 1

        return split_locations

    @staticmethod
    def get_location(info):
        return info[info.index("around") + 1 :]

    @staticmethod
    def code(a, _dict):
        for location_string in a:
            if location_string in _dict:
                return _dict.get(location_string)

        return "N/A"
