from typing import Literal, Optional
import requests
from onshape_api.base import BASE_URL, BaseOnshapeAPI, api_request


class OnshapeDocumentAPI(BaseOnshapeAPI):
    def __init__(self, access_key: str, private_key: str):
        super().__init__(access_key, private_key, "documents")

    @api_request
    def get_document(self, document_id: str):
        return self.session.get(
            f"{BASE_URL}/{self._url_extension}/{document_id}", auth=self._auth
        )

    @api_request
    def get_elements(
        self,
        document_id: str,
        wvm: Literal["w", "v", "m"],
        wvm_id: str,
        link_document_id: Optional[str] = None,
        element_type: Optional[str] = None,
        element_id: Optional[str] = None,
        with_thumbnails: bool = False,
    ):
        request_url = (
            f"{BASE_URL}/{self._url_extension}/d/{document_id}/{wvm}/{wvm_id}/elements"
        )
        payload: dict = {"withThumbnails": with_thumbnails}
        if element_type is not None:
            payload["elementType"] = element_type
        if link_document_id is not None:
            payload["linkDocumentId"] = link_document_id
        if element_id is not None:
            payload["elementId"] = element_id

        return self.session.get(request_url, auth=self._auth, params=payload)
