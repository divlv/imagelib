#
from modules import ilmodule
import requests
import os
import time
import globals


class DescribeImage(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        self.analyze_api_url = "https://northeurope.api.cognitive.microsoft.com/vision/v2.0/analyze?visualFeatures=Tags,Description"

        self.service_key = os.environ["AZURE_SERVICE_DESCRIPTION_KEY"]

        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_DESCRIBE_IMAGE)

    def onMessage(self, arg):
        self.getLogger().debug("Received message: " + str(arg))
        # Prevent too many requests to the API
        self.getLogger().debug(
            "Prevent too many requests to the API. Waiting for 5 seconds..."
        )
        time.sleep(5)
        self.describeImage(arg)

    def describeImage(self, image_data):

        sourceFile = image_data["image_path"]
        image_data["description"] = ""
        image_data["tags"] = []

        self.getLogger().info("Finding image description: " + str(sourceFile))
        try:
            headers = {
                # Request headers
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.service_key,
            }
            params = {}  # passed in URL

            image_bytes = self.getImageData(sourceFile)

            response = requests.post(
                self.analyze_api_url,
                params=params,
                headers=headers,
                data=image_bytes,
                stream=True,
            )

            analysis = response.json()

            if "error" in analysis:
                raise Exception(analysis["error"]["message"])

            self.getLogger().debug(str(analysis["description"]))

            if "tags" in analysis["description"]:
                image_data["tags"] = analysis["description"]["tags"]

            if analysis["description"]["captions"]:
                image_data["description"] = analysis["description"]["captions"][0][
                    "text"
                ]

            self.getMessageBus().sendMessage(globals.TOPIC_GPS, arg=image_data)

        except Exception as e:
            self.getLogger().error(str(e))
        finally:
            self.cleanupTmp()
