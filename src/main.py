from app import App
from purchasing_power import run

if __name__ == '__main__':
    occupation_data = run()
    dashboard = App(occupation_data)
    dashboard.start()