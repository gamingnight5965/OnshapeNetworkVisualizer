import os
from typing import Annotated, Literal, Optional
from onshape_api.base import BASE_URL, BaseOnshapeAPI, api_request
import json
import requests


class OnshapePartStudioAPI(BaseOnshapeAPI):
    def __init__(self, access_key: str, private_key: str):
        super().__init__(access_key, private_key, "partstudios")

    @api_request
    def get_features(
        self,
        document_id: str,
        wvm: Literal["w", "v", "m"],
        wvm_id: Annotated[str, "Id for (w)orkspace, (v)ersion, or (m)icroversion"],
        element_id: str,
        link_document_id: Optional[str] = None,
        configuration: Annotated[
            Optional[str],
            "URL-encoded string of configuration values (separated by ';'). See the [configutation API Guide](https://onshape-public.github.io/docs/api-adv/configs/)",
        ] = None,
        rollback_bar_index: int = -1,
        part_ids: Optional[list[str]] = None,
        include_surfaces: bool = False,
        include_composite_parts: bool = False,
        include_geometric_data: bool = True,
    ):
        path = f"./.cache/{document_id}-{wvm_id}-{element_id}.json"
        if os.path.exists(path):
            return open(path).read()

        request_url = f"{BASE_URL}/{self._url_extension}/d/{document_id}/{wvm}/{wvm_id}/e/{element_id}/features"
        payload: dict = {
            "rollbackBarIndex": rollback_bar_index,
            "includeSurfaces": include_surfaces,
            "includeCompositeParts": include_composite_parts,
            "includeGeometricData": include_geometric_data,
        }
        if part_ids is not None:
            payload["partIds"] = part_ids
        if link_document_id is not None:
            payload["linkDocumentId"] = link_document_id
        if configuration is not None:
            payload["configuration"] = configuration

        return self.session.get(request_url, params=payload, auth=self._auth)
