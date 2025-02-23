import uvicorn

if __name__ == '_main_':
    uvicorn.run('app.api:app', host = '0.0.0.0', port = 8000, reload = True)
