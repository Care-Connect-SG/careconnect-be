import asyncio
import nest_asyncio
import uvicorn

from api.index import app

nest_asyncio.apply()


async def run_backend():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, reload=False)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        run_backend(),
    )


if __name__ == "__main__":
    asyncio.run(main())
