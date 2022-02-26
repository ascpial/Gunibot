from gunibot import Gunibot
import logging

def run():
    # mise en place de l'output
    logging.basicConfig(
        level=logging.INFO,
    )
    
    # création de l'instance
    bot = Gunibot()
    
    bot.load_extension("extensions.hello_world")
    bot.load_extension("extensions.reminders")
    
    bot.run()

if __name__ == "__main__":
    run()