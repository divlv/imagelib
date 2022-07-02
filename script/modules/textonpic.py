#
from modules import ilmodule
import requests
import os
import time
import globals


class TextOnPicture(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        self.analyze_api_url_en = "https://northeurope.api.cognitive.microsoft.com/vision/v3.1/ocr?detectOrientation=true&language=en"
        self.analyze_api_url_ru = "https://northeurope.api.cognitive.microsoft.com/vision/v3.1/ocr?detectOrientation=true&language=ru"

        self.service_key = os.environ["AZURE_SERVICE_DESCRIPTION_KEY"]

        self.getMessageBus().subscribe(self.onMessage, globals.TOPIC_TEXT)

    def onMessage(self, arg):
        self.getLogger().debug("Received message: " + str(arg))
        # Prevent too many requests to the API
        self.getLogger().debug(
            "Prevent too many requests to the API. Waiting for 3 seconds..."
        )
        time.sleep(3)
        self.findTextOnImage(arg)

    def concatenateTextPieces(self, json_structure):
        text = ""

        if "regions" in json_structure:
            for region in json_structure["regions"]:
                for line in region["lines"]:
                    for word in line["words"]:
                        text += word["text"] + " "
        return text

    def findTextOnImage(self, image_data):
        sourceFile = image_data["image_path"]
        self.getLogger().info("Finding text on image: " + str(sourceFile))
        try:
            headers = {
                # Request headers
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.service_key,
            }
            params = {}  # passed in URL

            image_bytes = self.getImageData(sourceFile)

            response = requests.post(
                self.analyze_api_url_en,
                params=params,
                headers=headers,
                data=image_bytes,
                stream=True,
            )

            textanalysis_en = response.json()

            # Concatenate text from all regions
            text_en = self.concatenateTextPieces(textanalysis_en)

            self.getLogger().debug(
                "Prevent too many requests to the API. Waiting for 3 seconds between languages..."
            )
            time.sleep(3)

            response = requests.post(
                self.analyze_api_url_ru,
                params=params,
                headers=headers,
                data=image_bytes,
                stream=True,
            )

            textanalysis_ru = response.json()

            # Concatenate text from all regions
            text_ru = self.concatenateTextPieces(textanalysis_ru)

            image_data["text_en"] = text_en
            image_data["text_ru"] = text_ru

            self.getLogger().debug("Text on image EN: " + str(text_en))
            self.getLogger().debug("Text on image RU: " + str(text_ru))

            self.getMessageBus().sendMessage(globals.TOPIC_DATE, arg=image_data)

        except Exception as e:
            self.getLogger().error(str(e))
        finally:
            self.cleanupTmp()
