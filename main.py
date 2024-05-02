import pytz
import logging

from time import sleep
from typing import Any, Dict, List, Tuple
from requests import Session, Response
from datetime import datetime, timedelta

from fastapi.routing import serialize_response
from fastapi import FastAPI, Request, HTTPException

from app.routes import load_routes, EndpointConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = Session()
fast_app = FastAPI()


@fast_app.get("/")
async def main():
    return {"msg": "MyGateway is Alive"}


def call_http_url(**kwargs):
    request = kwargs.get("request")
    retries: int = 0
    # headers = sanitize_request_headers(extra_headers=extra_headers)
    while True:
        breakpoint()
        response = session.request(
            # method,
            # f"{base_url}{path}",
            data=request.body if request.body.getbuffer().nbytes > 0 else {},
            headers=request.headers,
            params=request.query.decode().dict if request.query else {},
            stream=True,
        )
        if (
            retries < 5
            and response.status_code == 400
            and "json" in response.headers.get("Content-Type")
            and "chunked" in response.text
        ):
            retries += 1
            sleep(0.1)
        else:
            break

    if retries:
        response.headers.append("x-retries", retries)
    return response


# subapi = APIRouter()


@fast_app.route("/<path>")
def call(request: Request):
    breakpoint()
    return call_http_url(request=request)


async def make_request(request: Request, target_api: str, path: str = "") -> Tuple[int, Dict[str, Any]]:
    retries: int = 0
    method = request.method
    url: str = target_api + path
    start_time: datetime = datetime.now().astimezone(pytz.UTC)
    breakpoint()
    while retries < 5:
        resp: Response = session.request(
            method=method,
            url=url,
            params=request.query_params._dict,
            # headers=dict(request.headers),
            # data=request.body if request.body else None,
            stream=True,
        )
        if (
            retries < 5
            and resp.status_code == 400
            and "json" in resp.headers.get("Content-Type")
            and "chunked" in resp.text
        ):
            breakpoint()
            retries += 1
            sleep(0.1)
            continue
        break
    breakpoint()
    resp = resp.iter_content(chunk_size=32768)
    end_time: datetime = datetime.now().astimezone(pytz.UTC)
    duration: timedelta = end_time - start_time
    resp.headers["X-Request-Duration"] = duration.total_seconds()
    breakpoint()
    return resp


def is_valid_jwt_token(token: str, extras: Dict[str, Any] = {}) -> bool:
    import jwt

    if token.startswith("Bearer"):
        token = token.split(" ")[-1]

    token_header: Dict[str, Any] = jwt.get_unverified_header(token)
    jwt.decode(token, algorithms=token_header.get("alg", "RS256"))

    return True


endpoints: List[EndpointConfig] = load_routes("endpoints.json", "./")


for endpoint_config in endpoints:
    print(endpoint_config)
    @fast_app.route(f"/{endpoint_config.endpoint}", methods=endpoint_config.verbs)
    async def interaction_handler(request: Request):
        breakpoint()
        if endpoint_config.is_public is False:
            try:
                is_valid_jwt_token(request.headers.get("authorization"))
            except Exception as err:
                logging.error(str(err))
                raise HTTPException(401, "InvalidToken")

        path: str = request.url.path.strip(f"/{endpoint_config.endpoint}")
        try:
            resp = make_request(request=request, target_api=endpoint_config.target_api, path=path)
        except:
            return
        return resp

    fast_app.add_api_route(
        f"/{endpoint_config.endpoint}",
        endpoint=interaction_handler,
        methods=endpoint_config.verbs,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:fast_app", workers=1)
