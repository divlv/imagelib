# Main processing script for the image processing pipeline.

from modules import ilmodule
from modules import facefinder


class Main(ilmodule.ILModule):
    def __init__(self):
        super().__init__()
        self.ff = facefinder.FaceFinder()

    def run(self):
        self.getLogger().info("Starting main loop")

        self.getMessageBus().sendMessage(
            "topic1", arg={"ssss": "sdsdsdsd", "news": "ddddddddddd"}
        )


if __name__ == "__main__":
    main = Main()
    main.run()
