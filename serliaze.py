import datetime
from enum import Enum


class Slot:
    SLOT_MAP = {
        1: datetime.time(8, 30),
        2: datetime.time(10, 15),
        3: datetime.time(11, 45),
        4: datetime.time(13, 45),
        5: datetime.time(15, 45),
    }

    def __init__(self, slot):
        self.start_time = self.SLOT_MAP[slot]
        # add 1 hour and half an hour
        self.end_time = datetime.datetime.combine(
            datetime.date.today(), self.start_time
        ) + datetime.timedelta(hours=1, minutes=30)
        self.end_time = self.end_time.time()

    def __str__(self):
        return f"{self.start_time}-{self.end_time}"


class Session:
    def __init__(self):
        self.location: str = ""
        self.slot: Slot = None
        self.instructor: Person = Person()
        self.course_code: str = ""
        self.group: str = ""
        self.week_day = None
        self.type: TYPE = TYPE.LAB
        self.course_name: str = ""

    def __str__(self):
        return f"{self.location} {self.slot} {self.instructor} {self.course_code} {self.group} {self.week_day} {self.type}"

    def next_weekday(self, d, weekday):
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return d + datetime.timedelta(days_ahead)

    def export_to_google_calendar(self):
        rows = []
        start_date = self.next_weekday(datetime.date.today(), self.week_day)
        print(self)
        end_date = start_date
        start_time = self.slot.start_time
        end_time = self.slot.end_time
        # generate event for each week
        for _ in range(1, 4):
            start_date = start_date + datetime.timedelta(weeks=1)
            end_date = end_date + datetime.timedelta(weeks=1)
            event = f"{self.course_name},{start_date},{start_time},{end_date},{end_time},{self.instructor},{self.location},True"
            rows.append(event)
        return rows


class Person:
    def __init__(self):
        self.name = None
        self.email = None

    def __str__(self):
        return f"{self.name} {self.email}"


class TYPE(Enum):
    LECTURE = 1
    LAB = 2
    TUTORIAL = 3


class SessionDeserializer:
    """
    Given a dictionary, return a Session object

    param data: a dictionary containing the data to be deserialized
    [
        "course_code": "CSC108H1F",
        "group": "L0101",
        type: "LAB",
        sessions: [
            {
                "x" : 1,
                "y" : 2,
                "location" : "BA 1202",
                "staff" : [
                    {
                        "name" : "John Doe",
                        "email" : ""
                    }
                ]
            }
        ]
    ]

    """

    def __init__(self):
        self.data: dict = {}

    def deserialize(self, data: dict) -> Session:
        session = Session()
        session.course_code = data["course_code"]
        session.group = data["tut_group"]
        session.type = self.get_type(data["type"])
        session.location = data["sessions"][0]["location"]
        session.slot = Slot(data["sessions"][0]["y"] + 1)
        session.week_day = self.get_day(data["sessions"][0]["x"] + 1)
        try:
            session.instructor.name = data["sessions"][0]["staff"][0]["name"]
        except IndexError:
            session.instructor.name = "Unknown"
        try:
            session.instructor.email = data["sessions"][0]["staff"][0]["email"]
        except IndexError:
            session.instructor.email = "Unknown"
        session.course_name = data["course_name"]
        return session

    def get_type(self, type: str) -> TYPE:
        if type == "Practical":
            return TYPE.LAB
        elif type == "Lecture":
            return TYPE.LECTURE
        elif type == "Tutorial":
            return TYPE.TUTORIAL
        else:
            raise ValueError("Invalid type")

    def get_day(self, day: int):
        # convert the index to a day of the week
        if day == 1:
            # saturday
            return 5
        elif day == 2:
            # sunday
            return 6
        elif day == 3:
            # monday
            return 0
        elif day == 4:
            # tuesday
            return 1
        elif day == 5:
            # wednesday
            return 2
        elif day == 6:
            # thursday
            return 3
        elif day == 7:
            # friday
            return 4


def get_json_data(id):
    import requests

    url = f"https://europe-west1-gucschedule.cloudfunctions.net/get_student_schedule/?id={id}"
    response = requests.get(url)
    return response.json()


if __name__ == "__main__":
    id = input("Enter your student id: ")
    data = get_json_data(id)["data"]
    session_deserializer = SessionDeserializer()
    rows = []
    rows.append(
        "Subject,Start Date,Start Time,End Date,End Time,Description,Location,Private"
    )
    for d in data:
        session = session_deserializer.deserialize(d)
        rows.extend(session.export_to_google_calendar())

    with open(f"guc-schedule-{id}.csv", "w") as f:
        f.write("\n".join(rows))
