from curl_cffi.requests import AsyncSession

class HTTPException(Exception):
    response: dict[str] | None
    status_code: int | None


    def __init__(self, response: dict[str] | None = None, status_code: int | None = None) -> None:
        self.response = response
        self.status_code = status_code


def aiohttp_params(params: dict[str] | None) -> dict[str, str | int | float] | None:
    new_params = params.copy() if params else None
    if not params:
        return

    for key, value in params.items():
        if value is None:
            del new_params[key]

        if isinstance(value, bool):
            new_params[key] = str(value).lower()

        elif isinstance(value, bytes):
            new_params[key] = value.decode('utf-8')

    return new_params


async def async_get(url: str, headers: dict | None = None, **kwargs) -> dict | None:
    """
    Make a GET request and check if it was successful.
    """
    async with AsyncSession(verify=False) as session:
        response = await session.get(
            url=url,
            headers=headers,
            **kwargs,
        )
        status_code = response.status_code
        response = response.json()
        if status_code <= 201:
            return response
        raise HTTPException(response=response, status_code=status_code)