#
from modules import ilmodule
import requests
import os
import time
import pickledb


class FaceFinder(ilmodule.ILModule):
    def __init__(self):
        super().__init__()

        self.people_db = "g:\Projects\imagelib\db\people.pdb"
        self.db = pickledb.load(self.people_db, False)

        self.face_api_url_prefix = (
            "https://northeurope.api.cognitive.microsoft.com/face/v1.0"
        )

        self.face_api_service_key = os.environ["AZURE_SERVICE_FACE_API_KEY"]
        self.person_group = "ourfaces"
        self.getMessageBus().subscribe(self.onMessage, "topic1")

    def onMessage(self, arg):
        self.log.info("Received message: " + str(arg))

    def extractFileName(self, filePath):
        return os.path.basename(filePath)

    def findFacesOnPicture(self, sourceFile):

        self.log.info("Finding faces on picture: " + str(sourceFile))
        self.log.debug("Using people database from: " + self.people_db)

        face_detect_url = self.face_api_url_prefix + "/detect"
        # No "targetFace" means there is only one face detected in the entire image !
        face_identify_url = self.face_api_url_prefix + "/identify"

        params = {"returnFaceId": "true"}

        facesOnPicture = []
        try:
            data = self.getImageData(sourceFile)
            headers = {
                "Content-Type": "application/octet-stream",
                "Ocp-Apim-Subscription-Key": self.face_api_service_key,
            }
            params = {"returnFaceId": "true", "returnFaceLandmarks": "true"}

            response = requests.post(
                face_detect_url, params=params, headers=headers, data=data
            )
            faceIds = []
            if response.status_code == self.HTTP_OK:
                faces = response.json()
                for f in faces:
                    faceIds.append(f["faceId"])
                self.log.debug("Faces on picture:" + str(faceIds))
            else:
                self.log.error("Error finding faces! " + response.text)

            self.log.debug("Preserve rate limit... (sleep(1))")
            time.sleep(1)
            #
            #
            if len(faceIds) > 0:
                headers = {
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": self.face_api_service_key,
                }

                r = requests.post(
                    face_identify_url,
                    headers=headers,
                    json={
                        "personGroupId": self.person_group,
                        "faceIds": faceIds,
                        "maxNumOfCandidatesReturned": "1",
                        "confidenceThreshold": "0.5",
                    },
                )
                if r.status_code == self.HTTP_OK:
                    self.log.debug("Some face(s) identified.")
                    identifiedFaces = r.json()
                    for idf in identifiedFaces:
                        for candidate in idf["candidates"]:
                            self.log.debug(
                                "Detected: " + self.db.get(candidate["personId"])
                            )
                            facesOnPicture.append(self.db.get(candidate["personId"]))
                else:
                    self.log.error("Error response code: " + str(r.status_code))
                    self.log.error(r.text)
            else:
                self.log.warning("No faces on photo.")
        except Exception as e:
            self.log.error("Error: " + str(e))
        finally:
            self.cleanupTmp()
            return facesOnPicture
