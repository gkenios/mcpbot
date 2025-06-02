from mcpbot.server.tools.common.joan_api import JoanAPI


def people_in_office(date: str, name: str | None = None) -> str:  # type: ignore[type-arg]
    """Find which people will be in the office on a given date. If a specific
    name is provided, only return information about that person. Respond with
    the full names, to avoid confusion with similar names.

    Args:
        date: The date of the reservation in the format "YYYY-MM-DD".
        name: The name of the person to check. Default is None, which means
            all people in the office will be returned, for that date.
    """
    api = JoanAPI()
    people = api.get_people_in_the_office(date, name)
    people_string = ", ".join(people)

    if name:
        if not people:
            return f"{people_string} is not in the office on {date}."
        else:
            return f"{people_string} is in the office on {date}."
    else:
        if not people:
            return f"No one is in the office on {date}."
        else:
            return f"People in the office on {date}: {people_string}."
