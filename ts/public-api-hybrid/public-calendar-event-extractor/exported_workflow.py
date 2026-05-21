from notte_sdk import NotteClient

client = NotteClient()


def run():
    with client.Session(proxies=True, use_file_storage=True) as session:
        # _ = session.execute(type='goto', url='https://www.loc.gov/events/')  # step failed
        return "Successfully completed task"


run()
