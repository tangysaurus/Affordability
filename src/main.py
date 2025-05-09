from app import App
from standard_of_living import run

if __name__ == '__main__':
    occupation_data = run()
    dashboard = App(occupation_data)
    dashboard.start()