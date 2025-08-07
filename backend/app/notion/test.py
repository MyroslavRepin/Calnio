from notion_client import Client
import os

notion = Client(auth="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")


database_id = "1bea555872b4810d8904df37389d5d18"


def get_tasks():
    response = notion.databases.query(database_id=database_id)
    tasks = []

    for page in response["results"]:
        props = page["properties"]

        name = props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "Без названия"
        complete = props[" Complete"]["checkbox"]
        description = props["Description"]["rich_text"][0]["plain_text"] if props["Description"]["rich_text"] else ""
        date_start = props["Date"]["date"]["start"] if props["Date"]["date"] else None
        date_end = props["Date"]["date"]["end"] if props["Date"]["date"] else None

        tasks.append({
            "name": name,
            "complete": complete,
            "description": description,
            "date_start": date_start,
            "date_end": date_end,
        })

    return tasks


if __name__ == "__main__":
    tasks = get_tasks()
    for task in tasks:
        print(f"📌 {task['name']}")
        print(f"   ✅ Выполнено: {'Да' if task['complete'] else 'Нет'}")
        print(f"   📝 Описание: {task['description']}")
        print(f"   📅 Дата: {task['date_start']} → {task['date_end']}\n")
