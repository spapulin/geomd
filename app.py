from pydantic import BaseModel, Field

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
import requests

import geomd as gmd
from geomd.registry import SrcFormat, DstFormat


app = FastAPI(
    title="geomd API",
    version=getattr(gmd, "__version__", "dev"),
    description="HTTP wrapper around the geomd library.",
)


_DICT_DST = {"json", "geojson"}
_HTTP_TIMEOUT = 30


class ConvertRequest(BaseModel):
    data: str = Field(..., description="The source document to convert.", examples=["{ GeoJSON }",])
    src: SrcFormat = Field(..., description="Source format.", examples=["geojson",])
    dst: DstFormat = Field(..., description="Destination format.", examples=["geomd",])


def _convert(data: str, src: SrcFormat, dst: DstFormat) -> Response:
    try:
        result = gmd.convert(
            text=data,
            src=src,
            dst=dst,
            as_dict=dst in _DICT_DST,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Provided data cannot be processed.",
        ) from exc

    if dst == "html":
        return HTMLResponse(result)
    return JSONResponse(result)


@app.get("/")
def convert_by_url(
    url: str,
    src: SrcFormat = Query(...),
    dst: DstFormat = Query(...),
) -> Response:
    """Convert the document provided by url from source
    to destination format."""
    try:
        response = requests.get(url, timeout=_HTTP_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch the source URL.",
        ) from exc
    return _convert(data=response.text, src=src, dst=dst)


@app.post("/")
def convert(req: ConvertRequest) -> Response:
    return _convert(data=req.data, src=req.src, dst=req.dst)
